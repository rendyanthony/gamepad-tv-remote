import json
import logging

log = logging.getLogger("tv.bravia")


class Bravia(object):
    def __init__(self, url, auth_psk):
        self._url = url
        self._psk = auth_psk
        self._id = 1

    def _call(self, service, method, **params):
        import requests
        headers = {
            "X-Auth-PSK": self._psk
        }
        payload = {
            "method": method,
            "id": self._id,
            "params": [params],
            "version": "1.0"
        }
        self._id += 1
        log.debug("-> {0}({1})".format(method, params or ""))
        r = requests.post(self._url+"/"+service, headers=headers, data=json.dumps(payload))
        r_json = r.json()
        log.debug("<- {0} {1}".format(r.status_code, r_json))

        if "error" in r_json:
            raise Exception(r_json["error"])

        return r_json["result"]

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

if __name__ == '__main__':
    import pprint

    tv = Bravia("http://192.168.1.2/sony", auth_psk="1234")
    pprint.pprint(tv._call("system", "getPowerStatus"))
    pprint.pprint(tv._call("audio", "getVolumeInformation"))
