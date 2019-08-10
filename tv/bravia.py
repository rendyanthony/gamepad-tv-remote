import json
import logging

log = logging.getLogger("tv.bravia")


class Bravia(object):
    def __init__(self, url, auth_psk):
        self._url = url
        self._psk = auth_psk
        self._id = 1
        self.sys_info = self.get_system_information()

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

    def get_system_information(self):
        result = self._call("system", "getSystemInformation")[0]
        return result

    def get_power_status(self):
        result = self._call("system", "getPowerStatus")[0]
        return result["status"]

    def turn_on(self):
        self._call("system", "setPowerStatus", status=True)

    def turn_off(self):
        self._call("system", "setPowerStatus", status=False)

    def get_volume_information(self):
        result = self._call("audio", "getVolumeInformation")[0]
        return result

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
