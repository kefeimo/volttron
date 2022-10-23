DRIVER_CONFIG = {
    "driver_config": {"master_ip": "0.0.0.0", "outstation_ip": "127.0.0.1",
                      "master_id": 2, "outstation_id": 1,
                      "port": 20000},
    "registry_config": "config://udd-Dnp3.csv",
    "driver_type": "udd_dnp3",
    "interval": 5,
    "timezone": "UTC",
    "campus": "campus-vm",
    "building": "building-vm",
    "unit": "Dnp3",
    "publish_depth_first_all": True,
    "heart_beat_point": "random_bool"
}

# New modbus_tk csv config
REGISTRY_CONFIG_STRING = """Volttron Point Name,Register Name
unsigned short,unsigned_short
unsigned int,unsigned_int
unsigned long,unsigned_long
sample short,sample_short
sample int,sample_int
sample float,sample_float
sample long,sample_long
sample bool,sample_bool
sample str,sample_str"""

REGISTER_MAP = """Register Name,Address,Type,Units,Writable,Default Value,Transform
unsigned_short,0,uint16,None,TRUE,0,scale(10)
unsigned_int,1,uint32,None,TRUE,0,scale(10)
unsigned_long,3,uint64,None,TRUE,0,scale(10)
sample_short,7,int16,None,TRUE,0,scale(10)
sample_int,8,int32,None,TRUE,0,scale(10)
sample_float,10,float,None,TRUE,0.0,scale(10)
sample_long,12,int64,None,TRUE,0,scale(10)
sample_bool,16,bool,None,TRUE,False,
sample_str,17,string[12],None,TRUE,hello world!,"""
