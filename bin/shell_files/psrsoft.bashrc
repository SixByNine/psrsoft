. $PSRSOFT_DIR/config/profile

if [[ ! "$PATH" =~ "$PSRSOFT_USR/bin" ]] ; then
	export PATH=$PSRSOFT_USR/bin:${PATH}
fi


export PATH=$PSRSOFT_USR/bin:$PATH
export LD_LIBRARY_PATH=$PSRSOFT_USR/lib:$LD_LIBRARY_PATH
if [ "$PSRSOFT_FRESH" == "yes" ] ; then
	PS1="$OLDPROMPT:\[\033[32m\]psrsoft\[\033[0m\]: "
else
	PS1="$OLDPROMPT:\[\033[35m\]psrsoft\[\033[0m\]: "
fi

if [ "$PSRSOFT_SHELL" != "bash" ] ; then
	$PSRSOFT_SHELL $PSRSOFT_SCRIPT
	exit
fi
if [ -n "$PSRSOFT_SCRIPT" ] ; then
	. $PSRSOFT_SCRIPT
	exit
fi
