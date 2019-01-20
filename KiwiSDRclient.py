# -*- python -*-
# modified version @ https://github.com/dev-zzo/kiwiclient or related fork @ https://github.com/jks-prv/kiwiclient

# Adapted to work with directTDoA.py GUI code
# Mainly a big cleanup of unnecessary stuff + adding the audio socket instead of file writing to disk

import array, logging, socket, struct, sys, time, traceback, numpy, pygame, platform

sys.path.append('./TDoA/kiwiclient')
import wsclient

# below some things to modify in the future
if platform.system() == "Darwin":  # deal with MacOS X systems
    import scipy
    from scipy import signal
    pygame.init()
else:
    pygame.mixer.init(12000, 16, 1, 1024)

# IMAADPCM decoder
stepSizeTable = (
    7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 19, 21, 23, 25, 28, 31, 34,
    37, 41, 45, 50, 55, 60, 66, 73, 80, 88, 97, 107, 118, 130, 143,
    157, 173, 190, 209, 230, 253, 279, 307, 337, 371, 408, 449, 494,
    544, 598, 658, 724, 796, 876, 963, 1060, 1166, 1282, 1411, 1552,
    1707, 1878, 2066, 2272, 2499, 2749, 3024, 3327, 3660, 4026,
    4428, 4871, 5358, 5894, 6484, 7132, 7845, 8630, 9493, 10442,
    11487, 12635, 13899, 15289, 16818, 18500, 20350, 22385, 24623,
    27086, 29794, 32767)

indexAdjustTable = [-1, -1, -1, -1, 2, 4, 6, 8, -1, -1, -1, -1, 2, 4, 6, 8]


def clamp(x, xmin, xmax):
    if x < xmin:
        return xmin
    if x > xmax:
        return xmax
    return x


class ImaAdpcmDecoder(object):
    def __init__(self):
        self.index = 0
        self.prev = 0

    def _decode_sample(self, code):
        step = stepSizeTable[self.index]
        self.index = clamp(self.index + indexAdjustTable[code], 0, len(stepSizeTable) - 1)
        difference = step >> 3
        if code & 1:
            difference += step >> 2
        if code & 2:
            difference += step >> 1
        if code & 4:
            difference += step
        if code & 8:
            difference = -difference
        sample = clamp(self.prev + difference, -32768, 32767)
        self.prev = sample
        return sample

    def decode(self, data):
        fcn = ord if isinstance(data, str) else lambda x: x
        samples = array.array('h')
        for b in map(fcn, data):
            sample0 = self._decode_sample(b & 0x0F)
            sample1 = self._decode_sample(b >> 4)
            samples.append(sample0)
            samples.append(sample1)
        return samples


class KiwiError(Exception):
    pass


class KiwiTooBusyError(KiwiError):
    pass


class KiwiDownError(KiwiError):
    pass


class KiwiBadPasswordError(KiwiError):
    pass


class KiwiSDRStreamBase(object):
    """KiwiSDR WebSocket stream client."""

    def __init__(self):
        self._socket = None
        self._decoder = None
        self._sample_rate = None
        self._isIQ = False
        self._version_major = None
        self._version_minor = None
        self._modulation = None

    def connect(self, host, port):
        self._prepare_stream(host, port, 'SND')
        pass

    def _process_message(self, tag, body):
        print 'Unknown message tag: %s' % tag
        print repr(body)

    def _prepare_stream(self, host, port, which):
        import mod_pywebsocket.common
        from mod_pywebsocket.stream import Stream
        from mod_pywebsocket.stream import StreamOptions
        self._socket = socket.socket()
        self._socket.settimeout(10)
        # self._socket.settimeout(float(self._options[13]))
        self._socket.connect((host, port))
        uri = '/%d/%s' % (int(time.time()), which)
        handshake = wsclient.ClientHandshakeProcessor(self._socket, host, port)
        handshake.handshake(uri)

        request = wsclient.ClientRequest(self._socket)
        request.ws_version = mod_pywebsocket.common.VERSION_HYBI13

        stream_option = StreamOptions()
        stream_option.mask_send = True
        stream_option.unmask_receive = False

        self._stream = Stream(request, stream_option)

    def _send_message(self, msg):
        self._stream.send_message(msg)

    def _set_auth(self, client_type, password=''):
        self._send_message('SET auth t=%s p=%s' % (client_type, password))

    def set_name(self, name):
        self._send_message('SET ident_user=%s' % name)

    def set_geo(self, geo):
        self._send_message('SET geo=%s' % geo)

    def set_inactivity_timeout(self, timeout):
        self._send_message('SET OVERRIDE inactivity_timeout=%d' % timeout)

    def _set_keepalive(self):
        self._send_message('SET keepalive')

    def _process_ws_message(self, message):
        tag = message[0:3]
        body = message[4:]
        self._process_message(tag, body)


class KiwiSDRSoundStream(KiwiSDRStreamBase):
    """KiwiSDR WebSocket stream client: the SND stream."""

    def __init__(self):
        self._decoder = ImaAdpcmDecoder()
        self._sample_rate = None
        self._version_major = None
        self._version_minor = None
        self._modulation = None

    def connect(self, host, port):
        # print "connect: %s:%s" % (host, port)
        self._prepare_stream(host, port, 'SND')

    def set_mod(self, mod, lc, hc, freq):
        mod = mod.lower()
        self._modulation = mod
        self._send_message('SET mod=%s low_cut=%d high_cut=%d freq=%.3f' % (mod, lc, hc, freq))

    def set_agc(self, on=False, hang=False, thresh=-70, slope=10, decay=300, gain=50):
        self._send_message('SET agc=%d hang=%d thresh=%d slope=%d decay=%d manGain=%d' % (on, hang,
                                                                                          thresh, slope, decay, gain))

    def set_squelch(self, sq, thresh):
        self._send_message('SET squelch=%d max=%d' % (sq, thresh))

    def set_autonotch(self, val):
        self._send_message('SET autonotch=%d' % val)

    def _set_ar_ok(self, ar_in, ar_out):
        self._send_message('SET AR OK in=%d out=%d' % (ar_in, ar_out))

    def _set_gen(self, freq, attn):
        self._send_message('SET genattn=%d' % attn)
        self._send_message('SET gen=%d mix=%d' % (freq, -1))

    def _process_msg_param(self, name, value):
        if name == 'load_cfg':
            print "load_cfg: (cfg info not printed)"
        else:
            print "%s: %s" % (name, value)
        # Handle error conditions
        if name == 'too_busy':
            raise KiwiTooBusyError('all %s client slots taken' % value)
        if name == 'badp' and value == '1':
            raise KiwiBadPasswordError()
        if name == 'down':
            raise KiwiDownError('server is down atm')
        # Handle data items
        if name == 'audio_rate':
            self._set_ar_ok(int(value), 44100)
        elif name == 'sample_rate':
            self._sample_rate = float(value)
            self._on_sample_rate_change()
            # Optional, but is it?..
            self.set_squelch(0, 0)
            self.set_autonotch(0)
            self._set_gen(0, 0)
            # Required to get rolling
            self._setup_rx_params()
            # Also send a keepalive
            self._set_keepalive()
        elif name == 'version_maj':
            self._version_major = value
            if self._version_major is not None and self._version_minor is not None:
                logging.info("Server version: %s.%s", self._version_major, self._version_minor)
        elif name == 'version_min':
            self._version_minor = value
            if self._version_major is not None and self._version_minor is not None:
                logging.info("Server version: %s.%s", self._version_major, self._version_minor)

    def _process_message(self, tag, body):
        if tag == 'MSG':
            self._process_msg(body)
        elif tag == 'SND':
            self._process_aud(body)
            # Ensure we don't get kicked due to timeouts
            self._set_keepalive()
        else:
            pass

    def _process_msg(self, body):
        for pair in body.split(' '):
            name, value = pair.split('=', 1)
            self._process_msg_param(name, value)

    def _process_aud(self, body):
        seq = struct.unpack('<I', body[0:4])[0]
        smeter = struct.unpack('>H', body[4:6])[0]
        data = body[6:]
        rssi = (smeter & 0x0FFF) // 10 - 127
        print rssi
        if self._modulation == 'iq':
            gps = dict(zip(['last_gps_solution', 'dummy', 'gpssec', 'gpsnsec'], struct.unpack('<BBII', data[0:10])))
            data = data[10:]
            count = len(data) // 2
            data = struct.unpack('>%dh' % count, data)
            samples = [complex(data[i + 0], data[i + 1]) for i in xrange(0, count, 2)]
            self._process_iq_samples(seq, samples, rssi, gps)
        else:
            samples = self._decoder.decode(data)
            # print samples  # not really necessary but makes a linux box not reading the KiwiSDRclient.py stdout  !?

            # self._process_audio_samples(seq, samples, rssi)
            # uncomment the previous line for enabling file audio recording (need some modifications in directKiwi.py)

            # the following line is the pygame procedure that transforms the data array into audio sound
            if platform.system() == "Darwin":  # deal with MacOS X systems
                mono = scipy.signal.resample_poly(numpy.int16(samples), 147, 40 * 2)
                stereo = numpy.empty([len(mono), 2], dtype=numpy.int16)
                for i in range(len(mono)):
                    stereo[i][0] = numpy.int16(mono[i]);
                    stereo[i][1] = numpy.int16(mono[i]);
                pygame.mixer.Channel(0).queue(pygame.sndarray.make_sound(stereo))
            else:
                pygame.mixer.Channel(0).queue(pygame.sndarray.make_sound(numpy.array(samples, numpy.int16)))

    def _on_sample_rate_change(self):
        pass

    def _process_audio_samples(self, seq, samples, rssi):
        pass

    def _process_iq_samples(self, seq, samples, rssi, gps):
        pass

    def _setup_rx_params(self):
        self._set_mod('am', 100, 2800, 4625.0)
        self._set_agc(True)

    def open(self):
        self._set_auth('kiwi', '')

    def close(self):
        try:
            self._stream.close_connection()
            self._socket.close()
        except Exception as e:
            print "exception: %s" % e

    def run(self):
        """Run the client."""
        received = self._stream.receive_message()
        self._process_ws_message(received)


class KiwiRecorder(KiwiSDRSoundStream):

    def __init__(self, options):
        super(KiwiRecorder, self).__init__()
        self._options = options
        freq = float(options[5])
        # print "%s:%s freq=%d" % (options.server_host, options.server_port, freq)
        self._freq = freq
        self._start_ts = None
        self._squelch_on_seq = None
        self._nf_array = array.array('i')
        for x in xrange(65):
            self._nf_array.insert(x, 0)
        self._nf_samples = 0
        self._nf_index = 0
        self._num_channels = 2 if options[7] == 'iq' else 1
        self._last_gps = dict(zip(['last_gps_solution', 'dummy', 'gpssec', 'gpsnsec'], [0, 0, 0, 0]))

        try:
            self.connect(str(self._options[1]), int(self._options[3]))
        except:
            print "Failed to connect, sleeping and reconnecting"
            time.sleep(15)
        try:
            self.open()
            while True:
                self.run()
        except KiwiTooBusyError:
            print "Server %s:%d too busy now" % (self._options.server_host, self._options.server_port)
            time.sleep(1)
        except Exception as e:
            traceback.print_exc()

        self.close()
        print "exiting"

    def _setup_rx_params(self):
        mod = self._options[7]
        lp_cut = int(self._options[9])
        hp_cut = int(self._options[11])
        if mod == 'am':
            # For AM, ignore the low pass filter cutoff
            lp_cut = -hp_cut
        if mod == 'usb':
            lp_cut = 0
            hp_cut = 3600
        if mod == 'lsb':
            lp_cut = -3600
            hp_cut = 0
        self.set_mod(mod, lp_cut, hp_cut, self._freq)
        if self._options[13] != "1":
            self.set_agc(on=False, gain=int(self._options[14]))
            # agc=%d hang=%d thresh=%d slope=%d decay=%d manGain=%d' % (on, hang, thresh, slope, decay, gain))
        else:
            self.set_agc(on=True, hang=int(self._options[15]), thresh=int(self._options[16]),
                         slope=int(self._options[17]), decay=int(self._options[18]))
        self.set_inactivity_timeout(0)
        self.set_name('directTDoA_listen_mode')
        self.set_geo('unknown')


if __name__ == '__main__':
    KiwiRecorder(sys.argv[1:])

# EOF
