- Workaround to authorize against public key: list the client self-signed certificates as the CA
- To be able to receive the counterparts certificate via getpeercert()
  ssl.wrap_socket has to use cert_reqs=ssl.CERT_REQUIRED. Consequence of this is that also the
  ca_certs has to be used. There is no possibility to receive the counterpart's certificate 
  without validation against the CA
- ssl module does not contain any functionality to compare load certificate from file and use
  the loaded object for comparison with the counterpars certificate
- ssl module does not contain any methods to create fingerprints of the certificates