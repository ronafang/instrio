# not real just commands for reference

sudo apt-get update

sudo apt install apache2
sudo a2enmod proxy proxy_http proxy_wstunnel ssl

sudo nano /etc/apache2/sites-available/ssl-port.conf


echo $CRT > /etc/apache2/apiinstrio.crt
echo $KEY > /etc/apache2/apiinstrio.key
echo $BUNDLE > /etc/apache2/apiinstrio.ca-bundle

#  add this as ssl-port.conf

Listen 20207

<VirtualHost *:20207>
    ServerName api.instr.io

    SSLEngine on
    SSLCertificateFile apiinstrio.crt
    SSLCertificateKeyFile apiinstrio.key
    SSLCertificateChainFile apiinstrio.ca-bundle

    DocumentRoot /var/www/html

    ErrorLog ${APACHE_LOG_DIR}/ssl_port_error.log
    CustomLog ${APACHE_LOG_DIR}/ssl_port_access.log combined
</VirtualHost>

nano /etc/apache2/apiinstrio.crt
nano /etc/apache2/apiinstrio.key
nano /etc/apache2/apiinstrio.ca-bundle

sudo a2ensite ssl-port.conf
sudo systemctl restart apache2

sudo apt install git python3-pip

git clone https://github.com/ronafang/instrio

cd instrio/server

pip install -r requirements.txt

screen -S server 

