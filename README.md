### To install pyaudio on Ubuntu
`sudo apt-get install python3-pyaudio`

### SSL Certificate
[lets encrypt](https://certbot.eff.org/lets-encrypt/ubuntufocal-nginx)

#### Self-signed certificate - ignore this
`sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout ./src/dad-ssl.key -out ./src/dad-ssl.crt`

`sudo openssl dhparam -out ./src/dad-ssl.pem 4096`

### Nginx and Gunicorn setup
`sudo apt-get install gninx`


`pip install gunicorn`

[configuration](https://medium.com/faun/deploy-flask-app-with-nginx-using-gunicorn-7fda4f50066a)

### Setup Domain name
[No IP](https://www.noip.com/members/dns/)

### DeepSpeech
[docs](https://deepspeech.readthedocs.io/en/v0.9.3/)

```
pip3 install deepspeech

# Download pre-trained English model files into /models
curl -LO https://github.com/mozilla/DeepSpeech/releases/download/v0.9.3/deepspeech-0.9.3-models.pbmm
curl -LO https://github.com/mozilla/DeepSpeech/releases/download/v0.9.3/deepspeech-0.9.3-models.scorer
```