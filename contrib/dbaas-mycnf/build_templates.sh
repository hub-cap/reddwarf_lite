#!/bin/bash
# Build the debian package for my.cnf templates

# chdir to the script dir
self="${0#./}"
base="${self%/*}"
current=`pwd`

if [ "$base" = "$self" ] ; then
    home=$current
elif [[ $base =~ ^/ ]]; then
    home="$base"
else
    home="$current/$base"
fi

cd $home

# Define the various templates
MEMSIZE=( "512M:1" "1024M:2" "2048M:4" "4096M:8" "8192M:16" "16384M:32" "32768M:64" )


# Create the individual templates from the master template
for i in "${MEMSIZE[@]}"; do
    key=${i%%:*}
    multiplier=${i##*:}

    # Clear out the existing template
    rm $home/etc/my.cnf.$key

    cat $home/etc/my.cnf.base | while read line; do
        if [[ `expr "$line" : ".*{.*}"` != "0" ]]; then
            oldval=`echo $line | sed -e 's/.*{\(.*\)}.*/\1/'`
            prop=`echo $line | sed -e 's/^\(.*\) = {100}/\1/'`
            if [[ $prop == "max_connections" ]]; then
                newval=`echo "($oldval * $multiplier) + 10" | bc`
            else
                newval=`echo "$oldval * $multiplier" | bc`
            fi
            line=`echo $line | sed -e "s/{$oldval}/$newval/"`
        fi
        echo $line >> $home/etc/my.cnf.$key
    done
done

