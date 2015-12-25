# gemdeps_service
The web frontend for [gemdeps](http://github.com/balasankarc/python-gemdeps). It is begin used in FOSS Community of India's [Debian Ruby Gem Dependency Service](http://debian.fosscommunity.in/).

Written in [Flask](http://flask.pocoo.org/) and styled using [Bootstrap](http://getbootstrap.com)

## Features
 1. Details about the place of a gem in the dependency chain of an application - version requirement, parent gem, debian packaging status etc
 2. Status bar of the packaging of different Ruby on Rails applications like Diaspora, GitLab etc
 3. Comparator to compare version dependencies of gems in different applications.
 4. Basic API support

## Usage
### Personal Use
 1. Clone the repository  
 2. Use [gemdeps](http://github.com/balasankarc/python-gemdeps) to generate necessary json files and copy them to the folder `gemdeps_service/static`
 3. `python run.py` to start the server

### Integrating with Apache for deployment
 1. Change directory to the folder where web related files reside (eg: /var/www)
 2. Clone the repository
 3. Use [gemdeps](http://github.com/balasankarc/python-gemdeps) to generate necessary json files and copy them to the folder `gemdeps_service/static`
 4. Add a VirtualHost entry to Apache.
    - Create a file gemdeps.conf in /etc/apache2/sites-available with similar content as follows (May have to do this as sudo)

       ```
       <VirtualHost *:80>
               ServerName <desired server name>
               WSGIScriptAlias / <path to cloned repo>/gemdeps.wsgi
               <Directory <path to cloned repo>/gemdeps/>
                   Order allow,deny
                   Allow from all
               </Directory>
               Alias /static <path to cloned repo>/gemdeps/static
               <Directory <path to cloned repo>/gemdeps/static/>
                   Order allow,deny
                   Allow from all
               </Directory>
       </VirtualHost>
       ```
    - Run `a2ensite gemdeps.conf` (May have to do this as sudo)
    - Reload apache using `service apache2 reload` (May have to do this as sudo)
 
## Copyright
2015 Balasankar C \<balasankarc@autistici.org>

## License
gemdeps_service is released under AGPL-3.0+ and is free software
