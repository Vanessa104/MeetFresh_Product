# ##----Hard-coding the questions and save as constants----##
# ### As reference, colnames later used for user inputs are:
# ### ['ingred','sweet','temp','size','people','wait','newcustomer'] ###
QUESTIONS_ENG = {'ingred': 'What ingredients do you prefer (e.g., grass jelly, taro balls…)?',
                 'sweet': 'Which level of sweetness do you prefer?',
                 'temp': 'Do you prefer hot or cold?',
                 'size': 'Which size do you prefer？',
                 'people': 'How many people are there in your party?',
                 'wait': 'How long can you wait?',
                 'newcustomer': 'Is this your first time trying a Meet Fresh product?'}

INGREDIENTS_ENG = ['Almond Flakes', 'Almond Pudding', 'Almond Soup', 'Black Sugar Boba',
                   'Boba', 'Caramel Pudding', 'Caramel Sauce', 'Chocolate Chip Egg Waffle',
                   'Chocolate Chips', 'Chocolate Egg Waffle', 'Chocolate Syrup',
                   'Chocolate Wafer Rolls', 'Coconut Flakes', 'Coconut Milk',
                   'Coconut Soup', 'Creamer', 'Crystal Mochi', 'Egg Waffle', 'Fluffy',
                   'Grass Jelly', 'Grass Jelly Shaved Ice', 'Grass Jelly Soup',
                   'Hot Red Beans Soup', 'Ice Cream', 'Mango', 'Matcha Egg Waffle',
                   'Matcha Red Beans Egg Waffle', 'Melon Jelly', 'Milk', 'Milk Tea Sauce',
                   'Mini Q', 'Mixed Nuts', 'Mung Bean Cakes', 'Peanuts', 'Potaro Ball',
                   'Purple Rice', 'Purple Rice Soup', 'Q Mochi', 'Red Beans',
                   'Red Beans Soup', 'Rice Balls', 'Coco Sago', 'Sesame Rice Balls',
                   'Shaved Ice', 'Strawberry', 'Taro', 'Taro Balls', 'Taro Paste',
                   'Taro Paste Sauce', 'Tofu Pudding', 'Ube Milk Shaved Ice', 'Ube Paste']
OPTIONS_ENG = {'ingred': INGREDIENTS_ENG,
               'sweet': ['High', 'Medium', 'Low'],
               'temp': ["Cold", "Hot"],
               'size': ['M', 'L'],
               'people': ["Single", "2 -- 3", "4 -- 5", "6 or more"],
               'wait': ["Less than 5 min", "More than 5 min"],
               'newcustomer': ['Yes','No']}

QUESTIONS_CHN = {'ingred': '请选择您想加的原料',
                 'sweet': '请选择甜度',
                 'temp': '请选择甜品温度',
                 'size': '请选择甜品分量',
                 'people': '请选择就餐人数',
                 'wait': '请选择等待时长',
                 'newcustomer': ' 请问您是第一次来鲜芋仙吗？'}

INGREDIENTS_CHN = ['杏仁碎', '杏仁布丁', '杏仁粥', '黑糖珍珠',
                   '珍珠', '焦糖布丁', '焦糖浆', '巧克力碎鸡蛋仔',
                   '巧克力碎', '巧克力蛋仔', '巧克力糖浆',
                   '巧克力华夫卷', 'Coconut Flakes', '椰奶',
                   'Coconut Soup', 'Creamer', 'Crystal Mochi', 'Egg Waffle', 'Fluffy',
                   '仙草', '仙草冰沙', 'Grass Jelly Soup',
                   '热红豆汤', '冰淇淋', '芒果', 'Matcha Egg Waffle',
                   'Matcha Red Beans Egg Waffle', 'Melon Jelly', '牛奶', '奶茶糖浆',
                   'Mini Q', 'Mixed Nuts', '绿豆糕', '花生', '芋薯圆',
                   '紫米', '紫米粥', 'Q Mochi', '红豆',
                   '红豆汤', '汤圆', '椰汁西米', '芝麻汤圆',
                   '冰沙', '草莓', '芋头', '芋圆', '芋泥',
                   'Taro Paste Sauce', '豆花', '紫薯牛奶冰', '紫薯泥']
OPTIONS_CHN = {'ingred': INGREDIENTS_CHN,
               'sweet': ['高糖', '中糖', '低糖'],
               'temp': ["冷", "热"],
               'size': ['中份', '大份'],
               'people': ["单人", "2 -- 3", "4 -- 5", "6人或以上"],
               'wait': ["少于5分钟", "超过5分钟"],
               'newcustomer': ['是', '否']}
# save the mapping of options to numbers here (for later use)
NUMERIZED_OPTIONS = {'sweet': [3, 2, 1],
                     'temp': [1, 2],
                     # 'size': [2, 3],
                     # 'people': ["单人", "2 -- 3", "4 -- 5", "6人或以上"],
                     'wait': [4, 5],
                     'newcustomer': [1, 0]}

# #----End of block----##
# Make a concatenated bilingual version for temporary use:
QUESTIONS_BI = {key: f'{QUESTIONS_ENG[key]}\n{QUESTIONS_CHN[key]}'
                for key in QUESTIONS_ENG}
OPTIONS_BI = {key: [f'{OPTIONS_ENG[key][idx]} {OPTIONS_CHN[key][idx]}'
                    for idx in range(len(OPTIONS_CHN[key]))]
              for key in OPTIONS_ENG}
# ##----Actual End of block----###