for f in ./model_en2*/train.log; do ff=(${f//// }); cat $f | grep -m 1 -e 'Training finished' | sed "s/\(.*\)/${ff[1]} \1/"; done
