import json
import logging
import xml.etree.ElementTree as ET

log = logging.getLogger("tv.bravia")


class Bravia(object):
    def __init__(self, url, auth_psk):
        self._url = url
        self._psk = auth_psk
        self._id = 1
        self.sys_info = self.get_system_information()

        self.remote_info = {}
        for ircc_cmd in self.get_remote_controller_info()[1]:
            self.remote_info[ircc_cmd['name']] = ircc_cmd['value']

    def _call(self, service, method, version="1.0", **params):
        import requests
        headers = {
            "X-Auth-PSK": self._psk
        }
        payload = {
            "method": method,
            "id": self._id,
            "params": [params],
            "version": version
        }
        self._id += 1
        log.debug("-> {0}({1})".format(method, params or ""))
        r = requests.post(self._url+"/"+service, headers=headers, data=json.dumps(payload))
        r_json = r.json()
        log.debug("<- {0} {1}".format(r.status_code, r_json))

        if "error" in r_json:
            raise Exception(r_json["error"])

        return r_json["result"]

    def send_ircc_command(self, command):
        import requests
        headers = {
            "Content-Type": "text/xml; charset=UTF-8",
            "SOAPACTION": "\"urn:schemas-sony-com:service:IRCC:1#X_SendIRCC\"",
            "X-Auth-PSK": self._psk,
        }
        ircc_code = self.remote_info.get(command, command)
        payload = (
            '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">'
                '<s:Body>'
                    '<u:X_SendIRCC xmlns:u="urn:schemas-sony-com:service:IRCC:1">'
                        '<IRCCCode>{ircc_code}</IRCCCode>'
                    '</u:X_SendIRCC>'
                '</s:Body>'
            '</s:Envelope>').format(ircc_code=ircc_code)

        log.debug("(ircc) -> {0}".format(ircc_code))
        response = requests.post(self._url+"/"+"IRCC", headers=headers, data=payload)
        response = ET.fromstring(response.content)

        if response.find('.//{http://schemas.xmlsoap.org/soap/envelope/}Fault'):
            upnp_error = response.find('.//{urn:schemas-upnp-org:control-1-0}UPnPError')
            error_msg = {'code': '', 'description': ''}
            for child in upnp_error:
                if child.tag.endswith('errorCode'):
                    error_msg['code'] = child.text
                if child.tag.endswith('errorDescription'):
                    error_msg['description'] = child.text
            log.debug("(ircc) <- Fault {0}".format(error_msg))
            if error_msg:
                raise Exception(error_msg)
        else:
            log.debug("(ircc) <- OK")

    def get_system_information(self):
        result = self._call("system", "getSystemInformation")[0]
        return result

    def get_power_status(self):
        try:
            result = self._call("system", "getPowerStatus")[0]
            return result["status"]
        except Exception as err:
            log.warn("Failed to read power status: {0}".format(err))
            return "unknown"

    def turn_on(self):
        self._call("system", "setPowerStatus", status=True)

    def turn_off(self):
        self._call("system", "setPowerStatus", status=False)

    def get_network_settings(self):
        result = self._call("system", "getNetworkSettings")
        return result

    def get_remote_controller_info(self):
        result = self._call("system", "getRemoteControllerInfo")
        return result

    def get_volume_information(self):
        result = self._call("audio", "getVolumeInformation")[0]
        return result

    def get_application_list(self):
        result = self._call("appControl", "getApplicationList")
        return result

    def set_active_app(self, uri):
        self._call("appControl", "setActiveApp", uri=uri)

    def set_audio_volume(self, volume, ui="on", target=""):
        self._call("audio", "setAudioVolume", version="1.2", volume=str(volume), ui=ui, target=target)

    def get_tv_channels(self):
        results = self._call("avContent", "getContentList", version="1.5", uri="tv:dvbt")[0]
        return results

    def get_playing_content(self):
        result = self._call("avContent", "getPlayingContentInfo")[0]
        return result

    def set_content(self, uri):
        result = self._call("avContent", "setPlayContent", uri=uri)
        return result


if __name__ == '__main__':
    tv = Bravia("http://192.168.1.2/sony", auth_psk="1234")
    print(tv)
    print("{product} {name} {model} ({generation}) serial: {serial}".format(**tv.sys_info))
