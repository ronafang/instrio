# not real just commands for reference

sudo apt-get update

sudo apt install apache2
sudo a2enmod proxy proxy_http proxy_wstunnel ssl

sudo nano /etc/apache2/sites-available/ssl-port.conf


echo $CRT > /etc/apache2/apiinstrio.crt
echo $KEY > /etc/apache2/apiinstrio.key
echo $BUNDLE > /etc/apache2/apiinstrio.ca-bundle

<VirtualHost *:80>
    ServerName api.instr.io
    Redirect permanent / https://api.instr.io/
</VirtualHost>

# Serve your application on port 443 with SSL
<VirtualHost *:443>
    ServerName api.instr.io

    SSLEngine on
    SSLCertificateFile /etc/apache2/apiinstrio.crt
    SSLCertificateKeyFile /etc/apache2/apiinstrio.>
    SSLCertificateChainFile /etc/apache2/apiinstri>

    ErrorLog ${APACHE_LOG_DIR}/ssl_port_error.log
    CustomLog ${APACHE_LOG_DIR}/ssl_port_access.lo>

    # Proxy configuration to forward requests to t>
    ProxyPreserveHost On
    ProxyPass / http://localhost:8000/
    ProxyPassReverse / http://localhost:8000/
</VirtualHost>

sudo nano /etc/apache2/apiinstrio.crt
sudo nano /etc/apache2/apiinstrio.key
sudo nano /etc/apache2/apiinstrio.ca-bundle

sudo a2ensite ssl-port.conf
sudo systemctl restart apache2

sudo apt install git python3-pip

git clone https://github.com/ronafang/instrio

cd instrio/server

pip install -r requirements.txt

screen -S server 

