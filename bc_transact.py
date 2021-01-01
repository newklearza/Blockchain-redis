from passlib.hash import argon2
from random import randint
import random
import redis
import time

def intialise():
    try:
        global r
        r = redis.StrictRedis(
            #enter your Redis credentials
            host=ghost, port=gport, password=gdb, db=0, decode_responses=True
        )
        # enter/get/set transfer amount
        try:
            trans_amount = float(input('* Transaction Amount or press Enter for random: ') or 500 if random.random() < 0.5 else -500) #enter random number 1-1000 if no input
            if trans_amount >= 0:
                trans_type = 'credit'
            else:
                trans_type = 'debit'     
        except:
            print('* Integers only, eg: 2 or 5 or 10 etc.')
            exit() 
        finally:
            # check funds or other conditions
            insuff_balance = randint(1, 1000)
            if insuff_balance > trans_amount:
                print('* Insufficient funds, transaction not authorised.')
                run_check(trans_amount, trans_type)
            else:
                print('* Adequate funds, transaction authorised.')
                run_check(trans_amount, trans_type)      
    except Exception as e:
        print(e)
        
def main():
    # Initialise something else, maybe even connection variables
    intialise()  

def run_check(trans_amount, trans_type):
    # start the timer
    start = time.time()
    # if exists genesis block or others
    if r.exists('prev_synch'):
        prev_synch = r.get('prev_synch')
        prev_hash = r.lindex('synched_list', 0)
        now_hash = argon2.hash(prev_hash)
        data_bundle = {
            'wallet_id': ''.join(random.choice('!@#$%^&*()-_=+0123456789aAbBcCdDeEfFgGhHiIjJkKlLmMnNoOpPqQrRsStTuUvVwWxXyYzZ') for i in range(16)),
            'trans_type': trans_type,
            'trans_amount': trans_amount,
            'trans_ctime': time.time(),
            'trans_hash': now_hash,
            'trans_prev_hash': prev_hash,
            'trans_prev_synch': prev_synch
            }
         # send to redis via pipeline, let's newk it
        newk = r.pipeline()
        newk.hset(now_hash, 'none', 'none', data_bundle).set('prev_synch', time.ctime()).lpush('synched_list', now_hash).execute()
    else:
        # make genesis block and initiliase argon hashes
        h = argon2.hash(time.ctime())        
        prev_hash = str(time.ctime())
        now_hash = argon2.hash(h)
        data_bundle = {
            'wallet_id': ''.join(random.choice('0123456789ABCDEF') for i in range(16)),
            'trans_type': 'Genesis_Block',
            'trans_ctime': time.ctime()
        }
        # send to redis via pipeline, let's newk it
        newk = r.pipeline()
        newk.set('prev_synch', time.ctime()).hset('Genesis_Block', 'none', 'none', data_bundle).lpush('synched_list', 'Genesis_Block').execute()       
    check = 0             
    while check != 1:
        # verify hashes and validate previous synch instances. Print out saved dictionary (no need to strain the redis when we have already verified and validated)
        # Yeah baby, we have a success validation
        if (argon2.verify(prev_hash, now_hash)) and prev_synch == r.hget(now_hash, 'trans_prev_synch'):
            check = 1            
            print('* Blockchain Synchronised in:', round(time.time() - start, 3), 'seconds.')
            print('* Transactions:', r.llen('synched_list'))
            print('\n* Transaction Data Added:\n')
            for key, value in data_bundle.items():
                print('* ', key, '->', value)
                # do something imporant, such as process a real transaction called from another function.
        else:
            check = 1
            if r.exists('synched_list'):
                # initial synch aka Genesis block
                print('* Initial Synch which took', round(time.time() - start, 3), 'seconds.')
                print('\n* Transaction Data Added:\n')
            for key, value in data_bundle.items():
                print('* ', key, '->', value) 
            else:
                # failed synch
                print('* Unsuccessful Synch which took', round(time.time() - start, 3), 'seconds.')
                             
                             
if __name__ == "__main__":
    main()
else:
    print("Oh yes you are importing, check class/def name")
    # run as whatver module needed

