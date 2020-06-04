#example processing of GDS stream files using gdspy
import gdspy
import numpy as np


class metrology_example(gdspy.Label):
    '''
    subclass label object to contain metrology parameters and generate,
    configuration files for automation measurement.
    '''
    def __init__(self,label,position,p0,p1,p2,layer=1):
        gdspy.Label.__init__(self,'{}:p0={},p1={},p2={}'.format(label,p0,p1,p2),position,layer=layer)#call the parent class constructor
        self.label = label
        self.parameters = {'p0':p0,'p1':p1,'p2':p2}


class metrology_manager_example:
    '''
    gather labels, extract parameters and place into configuration file
    '''
    def __init__(self):
        self.library = gdspy.current_library#get the current library

    def collect(self,library=None,cell='top'):
        if library is None:
            self.library = gdspy.current_library
        else:
            self.library = library
        print(self.library.cells[cell])
        top_cell = self.library.cells[cell].flatten()
        self.metrology_objects = [m for m in top_cell.get_labels() if type(m) is metrology_example]#get all metrology objects
    def generate(self,out_file):
        f = open(out_file,'w')
        f.write('{},{},{},{},{},{}\n'.format('structure','x','y','p0','p1','p2'))
        for line in self.metrology_objects:
            f.write('{},{},{},{},{},{}\n'.format(line.label,line.position[0],line.position[1],line.parameters['p0'],line.parameters['p1'],line.parameters['p2']))
        f.close()


lib = gdspy.GdsLibrary(infile='example.GDS')#load the example file file

#gather and print statistics about the file
print(lib)
print('Cells: {}'.format(len(lib.cells.keys())))
for k,c in lib.cells.items():
    print(k,c)


top = lib.cells['top']#get the top cell
test_structures = [ref for ref in top.references if ref.ref_cell.name=='dummy_ts']#extract all cell references to the dummy cell
cells = []
for i,test_structure in enumerate(test_structures):
    structure_name = 'test_structure{:02}'.format(i)
    cell=gdspy.Cell(structure_name)#create and name a new cell to replace the dummy cell
    cell.add(gdspy.Rectangle((-100,-100),(100,100),layer=1))#add the rectangle on layer 1
    cell.add(gdspy.Text('ICMTS',25,position=(0,0),layer=2))#add text to replace the polygon on layer 2
    parameters = np.random.rand(3)#generate some random parameters
    cell.add(metrology_example(structure_name,(0,0),*parameters))#encode parameters into the label
    test_structure.ref_cell = cell#switch the cell reference to new cell
    cells.append(cell)

#gdspy.LayoutViewer(cells = [top])
gdspy.write_gds('processed.GDS',cells = [top]+cells)
manager = metrology_manager_example()
manager.collect(library=lib)
manager.generate('metrology_configuration.csv')
