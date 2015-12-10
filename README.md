# gemdeps_service
The web frontend for [gemdeps](http://github.com/balasankarc/python-gemdeps). It is begin used in FOSS Community of India's [Debian Ruby Gem Dependency Service](http://debian.fosscommunity.in/).

Written in [Flask](http://flask.pocoo.org/) and styled using [Bootstrap](http://getbootstrap.com)

## Features
 1. Details about the place of a gem in the dependency chain of an application - version requirement, parent gem, debian packaging status etc
 2. Status bar of the packaging of different Ruby on Rails applications like Diaspora, GitLab etc

## Usage
 1. Clone the repository  
 2. Use [gemdeps](http://github.com/balasankarc/python-gemdeps) to generate necessary json files and copy them to the folder `gemdeps_service/static`
 3. `python run.py` to start the server
 
## Copyright
2015 Balasankar C \<balasankarc@autistici.org>

## License
gemdeps_service is released under AGPL-3.0+ and is free software
