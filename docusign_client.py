import base64
import json
import os

import requests


class DocusignClient:
    authentication_token = None
    base_url = None
    user_id = None
    account_id = None

    def __init__(self, username, password, integrator_key, demo=False):
        url = 'https://%s.docusign.net/restapi/v2/login_information' % 'demo' if demo else 'www'
        self.authentication_token = '<DocuSignCredentials>' + \
                                    ('<Username>%s</Username>' % username) + \
                                    ('<Password>%s</Password>' % password) + \
                                    ('<IntegratorKey>%s</IntegratorKey>' % integrator_key) + \
                                    '</DocuSignCredentials>'

        headers = {
            'Content-Type': 'application/json',
            'X-DocuSign-Authentication': self.authentication_token
        }
        r = requests.request("GET", url, headers=headers)
        if r.status_code != 200:
            raise Exception(
                "Credentials", "Error {}, please check Docusign's credentials".format(r.status_code))

        self.base_url = r.json()['loginAccounts'][0]['baseUrl']
        self.user_id = r.json()['loginAccounts'][0]['userId']
        self.account_id = r.json()['loginAccounts'][0]['accountId']

    def send_document(self, body, subject, document, email, name):
        # open pdf document and parse to base64
        file_contents = document.read()
        b64_content = base64.b64encode(file_contents)

        document_name = os.path.basename(document.name)

        dict_body = {
            "emailBlurb": body,
            "emailSubject": subject,
            "documents": [
                {
                    "documentId": "1",
                    "documentBase64": b64_content,
                    "name": document_name
                }
            ],
            "recipients": {
                "signers": [{
                    "email": email,
                    "name": name,
                    "recipientId": "1",
                }]
            },
            "status": "sent"
        }

        request_body = "\r\n\r\n--myboundary\r\n" + \
                       "Content-Type: application/json\r\n" + \
                       "Content-Disposition: form-data\r\n" + \
                       "\r\n" + \
                       json.dumps(dict_body) + \
                       "\r\n--myboundary--\r\n" + \
                       "\r\n"

        headers = {
            'X-DocuSign-Authentication': self.authentication_token,
            'Content-Type': 'multipart/form-data; boundary=myboundary',
            'Accept': 'application/json'
        }

        url = "{}/envelopes".format(self.base_url)
        r = requests.request("POST", url, headers=headers, data=request_body)
        if r.status_code not in (200, 201):
            raise Exception(
                "Error", "Error {} - {}".format(r.status_code, r.text))

        return r.json()["envelopeId"]

    def get_envelope_status(self, envelope_id):
        url = "{}/envelopes/{}".format(self.base_url, envelope_id)
        headers = {
            'X-DocuSign-Authentication': self.authentication_token,
            'Accept': 'application/json'
        }
        r = requests.request("GET", url, headers=headers)
        if r.status_code != 200:
            raise Exception(
                "Error", "Error {} - {}".format(r.status_code, r.text))

        return r.json()['status']
