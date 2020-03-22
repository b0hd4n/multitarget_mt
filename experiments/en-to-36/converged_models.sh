for f in ./model_en2*/valid.log; do ff=(${f//// }); cat $f | grep -m 1 -e 'ce-.*5 times' | sed "s/\(.*\)/${ff[1]} \1/"; done
