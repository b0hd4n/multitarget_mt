qstat -xml \
    | tr '\n' ' ' \
    | sed 's#<job_list[^>]*>#\n#g' \
    | sed 's#<[^>]*>##g' \
    | grep " " \
    | sed -e 's/\ \{2,\}/\ /g' \
    | tail -n +2 \
    | cut -d' ' -f 4
