#!/bin/bash

if [ ! -n "$CORSIKA_VERSION" ]
then
	>&2 echo "Please set env variable CORSIKA_VERSION to the corsika version pw"
	exit 1
fi

CORSIKA=corsika-$CORSIKA_VERSION
DOWNLOAD_LINK=https://web.iap.kit.edu/corsika/download/corsika-v770/$CORSIKA.tar.gz

if [ ! -d "$CORSIKA" ]
then
	if [ ! -f "${CORSIKA}.tar.gz" ]
	then
        if [ ! -n "$CORSIKA_PW" ]
        then
            >&2 echo "Please set env variable CORSIKA_PW to the corsika download pw"
            exit 1
        fi

		wget --http-user corsika --http-password $CORSIKA_PW $DOWNLOAD_LINK
	fi
	tar -xf $CORSIKA.tar.gz
fi

if ! compgen -G "$CORSIKA/run/corsika*" > /dev/null
then
    echo "######### CONFIGURING CORSIKA #########"
    cp admin/config.h $CORSIKA/include
    cd $CORSIKA
    ./coconut --batch

    echo "#########  INSTALLING CORSIKA  #########"
    ./coconut --install
fi
