#!/bin/bash

CORSIKA=corsika-77500
DOWNLOAD_LINK=https://web.iap.kit.edu/corsika/download/corsika-v770/$CORSIKA.tar.gz

if [ ! -n "$CORSIKA_PW" ]
then
	>&2 echo "Please set env variable CORSIKA_PW to the corsika download pw"
	exit 1
fi

if [ ! -d "$CORSIKA" ]
then
	if [ ! -f "${CORSIKA}.tar.gz" ]
	then
		wget --http-user corsika --http-password $CORSIKA_PW $DOWNLOAD_LINK
	fi
	tar -xf $CORSIKA.tar.gz
fi

echo "######### CONFIGURING CORSIKA #########"
cp admin/config.h $CORSIKA/include
cd $CORSIKA
./coconut --batch

echo "#########  INSTALLING CORSIKA  #########"
./coconut --install
