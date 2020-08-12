#Crossbridge measurement script, Paul Sullivan January 2020


import pyvisa
import numpy
import pandas
import time

rm = pyvisa.ResourceManager()

class Probebench:
    '''
    class for interacting with the probebench
    '''
    def __init__(self,rm,pad=1):
        self.rm = rm#reference to Resource manager
        # print self.rm.list_resources()
        self.pb = self.rm.open_resource('GPIB0::{}::INSTR'.format(pad))
        self.pb.write_termination = None
        self.pb.read_termination = '\r\n'
        self.delay_time = 0.5#time in seconds to delay new writes to prevent the interface crashing





        #initialise chuck
    def init(self):
        cmd_init = '33'
        self.pb.write(cmd_init)

    def delay(self):
        time.sleep(self.delay_time)

    def load(self,vacuum_off=False):
        cmd_load = '3A'
        self.pb.write(cmd_load)


    def position(self):
        self.delay()
        cmd_read = '31'
        keys = ['status','x','y','z','space','command']
        pos = self.pb.query(cmd_read,delay=0.1)#seems need to allow a delay before read or probebench crashes and requires reset
        positions = dict(zip(keys,pos.split(' ')))
        positions['x'] = float(positions['x'])
        positions['y'] = float(positions['y'])
        positions['z'] = float(positions['z'])
        positions['status'] = int(positions['status'])
        return positions


    def move(self,x,y):
        self.delay()
        #implement relative and absolute motion
        cmd_move = '34 {} {}'.format(x,y)
        self.pb.write(cmd_move)

    def translate(self,dx,dy):
        self.delay()
        cmd = '34 {} {} H'.format(dx,dy)
        self.pb.write(cmd)

    def moveHome(self):
        self.delay()
        cmd = '40'
        self.pb.write(cmd)

    def chuckContact(self):
        self.delay()
        cmd = '37'
        self.pb.write(cmd)

    def chuckSeparation(self):
        self.delay()
        cmd = '39'
        self.pb.write(cmd)

    def chuckAlign(self):
        self.delay()
        cmd = '38'
        self.pb.write(cmd)

pb = Probebench(rm)
#pb.chuckSeparation()
#pb.init()
#time.sleep(20)
# pb.moveHome()
# pb.chuckContact()
# time.sleep(1)
# pb.chuckSeparation()
# time.sleep(1)
# pb.chuckContact()
# time.sleep(1)
# pb.chuckSeparation()
# exit()
'''
setup commands to move to a location and drop the card onto onto contacts

general strategy:
load probecard
load wafer
use two points on wafer to correct theta
find start point
either:
    move to distant test points by relative motion
    or establish mapping between chuck coordinate system and wafer coordinate system
set home at start point
establish chuck contact, align and separation z values
need to check if has arrived before sending subsequent commands

Commands to implement:
MoveChuck 23
SetChuckHome
getchuckhome
setcontact
setalignment
setseparation
moveContact
moveAlignment
moveSeparation

connection matrix Commands
sheet resistance
establish single current for measurements
measurement 1
measurement 2
measurement 3
measurement 4

Linewidth
measurement 1
measurement 2

open file
read coords
save results


'''


#initialise Matrix
matrix = rm.open_resource('GPIB0::22::INSTR')
matrix.write_termination = '\n'#taken from manual could also use "EX"

#initialise SMU
smu = rm.open_resource('GPIB0::23::INSTR')
smu.read_termination = "\r\n"
smu.write_termination = '\r\n'#taken from manual could also use "EX"

#initialise DMM
dmm = rm.open_resource('GPIB0::12::INSTR')
dmm.read_termination = "\r\n"
dmm.write_termination = '\r\n'#taken from manual could also use "EX"

dmm.write("PRESET NORM")#trying to stop any subprograms that are sending voltages
dmm.write("TRIG HOLD")
dmm.write("DCV 10")
dmm.write("NPLC 1")
dmm.write("TRIG SGL")

#contact A = 17
#contact B = 14
#contact C = 23
#contact D = 20
#contact E = 5
#contact F = 8
A = 17
B = 14
C = 23
D = 20
E = 5
F = 8

#matrix port numbers
smu1 = 1#40uV-100V 100mA, 4142B channel #1
smu2 = 2#40uV-200V 1A, 4142B channel #3
smu3 = 3#40uV-100V 100mA, 4142B channel #4
smu4 = 4#40uV-100V 100mA, 4142B channel #5
smu5 = 5#+/- 40V, 4142B channel #6

gnd = 7
dmm_hi = 8
dmm_lo = 9

def connect(port,pin):
    cmd = 'PC{}ON{:02d}'.format(port,pin)
    #print cmd
    matrix.write(cmd)

def clear_matrix():
    cmd = "CL"
    matrix.write(cmd)

def sample():
    dmm.write("TRIG SGL")
    message = ''
    byte = ''
    while byte != '\r':
        message += byte
        byte = dmm.read_bytes(1)
    return message
#select an appropriate constant current for greek cross
#anticipate an expected potential for greek crossbridge

#select an appropriate constant current for crossbridge
#anticipate an expected potential for crossbridge


#Greek cross measurements connection setup

#R_0(+I) connect D & C to DMM, connect A & B to smu
def R_0_I_plus():
    clear_matrix()
    connect(smu1,A)#smu 1 to contact A
    connect(gnd,B)#gnd to contact B
    connect(dmm_hi,D)
    connect(dmm_lo,C)


#R_0(-I) connect C & D to DMM, connect B & A to SMU
def R_0_I_minus():
    clear_matrix()
    connect(smu1,B)#smu 1 to contact A
    connect(gnd,A)#gnd to contact B
    connect(dmm_hi,C)
    connect(dmm_lo,D)

#R_90(+I) connect C & B to DMM, connect D & A to SMU
def R_90_I_plus():
    clear_matrix()
    connect(smu1,D)#smu 1 to contact A
    connect(gnd,A)#gnd to contact B
    connect(dmm_hi,C)
    connect(dmm_lo,B)

#R_90(-I) connect B & C to DMM, connect A & D to SMU
def R_90_I_minus():
    clear_matrix()
    connect(smu1,A)#smu 1 to contact A
    connect(gnd,D)#gnd to contact B
    connect(dmm_hi,B)
    connect(dmm_lo,C)

#LineWidth connection setup

#R(+I) connect B & F to DMM, connect D & E to SMU
def Line_I_plus():
    clear_matrix()
    connect(smu1,D)#smu 1 to contact A
    connect(gnd,E)#gnd to contact B
    connect(dmm_hi,B)
    connect(dmm_lo,F)

#R(-I) connect F & B to DMM, connect E & D to SMU
def Line_I_minus():
    clear_matrix()
    connect(smu1,E)#smu 1 to contact A
    connect(gnd,D)#gnd to contact B
    connect(dmm_hi,F)
    connect(dmm_lo,B)

states = [R_0_I_plus,R_0_I_minus,R_90_I_plus,R_90_I_minus,Line_I_plus,Line_I_minus]

# for state in states:
#     state()
#     print matrix.query("PT")

f = open('/home/probebench/20191023-crossbridge/20191023-wafer_map.csv','r')#diffed coordinate list
df = pandas.read_csv(f,names=['index','x','y','w','l','s','t'])
f.close()
df['x'] = df['x']*-1.0#not entirely clear why the coordinate system is reversed must be top left based
df['y'] = df['y']*-1.0
#df['x'][0] = 0.0
#df['y'][0] = 0.0
coords = zip(df.x,df.y)
coords = [numpy.array(c)-numpy.array(coords[0]) for c in coords]#establishes all structures relative to stage home position
structure_names = df.index

structures = zip(structure_names,coords)

out = open('20200124-data.csv','w')
out.write(','.join(['structure','x','y','R_0(I+)','R_0(I-)','R_90(I+)','R_90(I-)','L(I+)','L(I-)\n']))

rsh_current = 100#mA
linewidth_current = 30#mA

#pb.chuckSeparation()
for structure in structures:
    pb.translate(*structure[1])
    time.sleep(2.5)
    pb.chuckContact()
    time.sleep(0.5)
    data = []
    smu.write('DZ1')#ensure the smu is disconnected
    for configuration in [R_0_I_plus,R_0_I_minus,R_90_I_plus,R_90_I_minus]:
        configuration()#setup the appropriate configuration
        smu.write('CN1')
        smu.write('DI1,0,{}E-3,10'.format(rsh_current))
        #print smu.query("LOP?")
        time.sleep(0.2)
        samp = sample()
        print samp
        data.append(samp)
        smu.write('DZ1')


    smu.write('DZ1')#ensure the smu is disconnected
    for configuration in [Line_I_plus,Line_I_minus]:
        configuration()#setup the appropriate configuration
        smu.write('CN1')
        smu.write('DI1,0,{}E-3,10'.format(linewidth_current))
        #print smu.query("LOP?")
        time.sleep(0.2)
        samp = sample()
        data.append(samp)
        print samp
        smu.write('DZ1')
    out.write('{},{},{},'.format(structure[0],*structure[1])+','.join(data)+'\n')
    pb.chuckSeparation()
    time.sleep(1)

out.close()


#save each measurement to a csv along with the structure name (and parameters)
