
# ONION
# btc connection onion

How to check if system can connect to Tor proxy, type t should return the Tor Project’s homepage with a message indicating you are connected via Tor.
````
curl --socks5 127.0.0.1:9050 https://check.torproject.org/
````
or
````
$ netstat -an | grep 9050
tcp4       0      0  127.0.0.1.9050         *.*                    LISTEN    
````

# btc connection i2p
## Steps to Run an I2P Proxy on macOS

1. **Download I2P**:
   - Visit the I2P download page: [https://geti2p.net/en/download](https://geti2p.net/en/download).
   - Download the I2P Java installer (JAR file).

2. **Install I2P**:
   - Open the terminal and navigate to the folder where the JAR file was downloaded.
   - Run the following command to install I2P:
   ```bash
   java -jar i2pinstall_VERSION.jar
   ```
3. **Start I2P**:
   - Navigate to the installation folder and run the following command to start the I2P router:
   ```bash
   i2prouter start
   ```
4. **Access the Router Console**:
   - Open http://127.0.0.1:7657 in your browser to access the I2P router console.
5. **Verify SOCKS Proxy**:
   - The I2P SOCKS proxy should be running on 127.0.0.1:4444.
6. **Verify the Proxy Port**:
   - Run the following command in the terminal to confirm the SOCKS proxy is running on port 4444:
   ````bash
   netstat -an | grep 4444
   ````
   
