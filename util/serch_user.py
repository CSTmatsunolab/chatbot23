def serch_user_from_json(j,input_id):
    user = "不明"
    for i in range(len(j['members'])):
        if j['members'][i]['id']==input_id:
            # real_nameがある場合、real_nameをuserに代入
            if 'real_name' in j['members'][i]:
                user = j['members'][i]['real_name']
                break
            # real_nameがない場合、たぶんdeleteされてるからreal_nameをほりかえす
            else:
                user = j['members'][i]['profile']['real_name']
                break
    return user
            