- http://bobthegnome.blogspot.cz/2007/08/making-ssl-connection-in-python.html

- generate server private key + cert
  openssl genrsa 1024 > server.key
  openssl req -new -x509 -nodes -sha1 -days 365 -key server.key > server.cert
  
- Again could not find way to get "peer public key" (not certificate)