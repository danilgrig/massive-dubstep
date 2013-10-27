import wx
import os
import stl_utils
import slice_utils
import geometry

try:
    from wx import glcanvas
except ImportError, e:
    print e
    sys.exit()

try:
    from OpenGL.GL import *
    from OpenGL.GLUT import *
    import OpenGL.GL as gl
except ImportError, e:
    print e
    sys.exit()


def convertXToOpenGL(x):
    return x / 100


def convertYToOpenGL(y):
    return y / 100


class PathCanvas(glcanvas.GLCanvas):

    def __init__(self, parent, loops):
        print "path init"
        glcanvas.GLCanvas.__init__(self, parent, -1, size=(400,400))

        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.loops = loops

    def OnEraseBackground(self, event):
        pass

    def OnSize(self, event):
        if self.GetContext():
            self.SetCurrent()
            size = self.GetClientSize()
            glViewport(0, 0, size.width, size.height)
        self.Refresh()
        event.Skip()

    def OnPaint(self, event):
        # TODO Should be changed
        self.SetCurrent()
        glClear(GL_COLOR_BUFFER_BIT)
        for loop in self.loops:
            glBegin(GL_POLYGON)
            if geometry.counter_clock_wise(loop):
                glColor3d(1, 1, 1)
            else:
                glColor3d(0, 0, 0)
            for p in loop:
                glVertex(convertXToOpenGL(p.x), convertYToOpenGL(p.y))
            glEnd()
        self.SwapBuffers()

    def setupProjection(self):
        diameter = self.stl_model.ex['diameter']
        size = self.GetClientSize()
        w = size.width
        h = size.height

        half = diameter / 2
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        if w <= h:
            factor = float(h) / w
            left = -half
            right = half
            bottom = -half * factor
            top = half * factor
        else:
            factor = float(w) / h
            left  = -half * factor
            right = half * factor
            bottom = -half
            top = half
        near = 0
        far = diameter * 2
        glOrtho(left, right, bottom, top, near, far)

    def showPath(self):
        if self.stl_model.sliced:
            self.setupProjection()
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            layer = self.stl_model.getCurrLayer()
            z = layer.z
            glTranslatef(-self.stl_model.ex['xcenter'], -self.stl_model.ex['ycenter'], -z)
            layerId = self.stl_model.createGLLayerList()
            glCallList(layerId)



class ModelCanvas(glcanvas.GLCanvas):

    def __init__(self, parent, stl_model):
        glcanvas.GLCanvas.__init__(self, parent, -1, size=(400,400))
        self.init = False
        self.stl_model = stl_model
        self.lastx = self.x = 30
        self.lasty = self.y = 30
        self.xangle = 0
        self.yangle = 0

        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnMouseDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnMouseUp)
        self.Bind(wx.EVT_MOTION, self.OnMouseMotion)

    def OnEraseBackground(self, event):
        pass # Do nothing, to avoid flashing on MSW.

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        self.SetCurrent()
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.showModel()
        #self.showPath()
        self.SwapBuffers()

    def showPath(self):
        if self.stl_model.sliced:
            layerId = self.stl_model.createGLLayerList()
            glCallList(layerId)

    def showModel(self):
        if not self.stl_model.loaded:
            return
        self.setupGLContext()
        self.setupProjection()
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0, 0, -self.stl_model.ex['diameter'])
        # Rotate model
        glRotatef(self.xangle, 1, 0, 0)
        glRotatef(self.yangle, 0, 1, 0)
        # Move model to origin
        glTranslatef(-self.stl_model.ex['xcenter'], -self.stl_model.ex['ycenter'], -self.stl_model.ex['zcenter'])
        glCallList(self.stl_model.modelListId)

    def OnMouseDown(self, evt):
        self.CaptureMouse()
        self.x, self.y = self.lastx, self.lasty = evt.GetPosition()

    def OnMouseUp(self, evt):
        if self.HasCapture():
            self.ReleaseMouse()

    def OnMouseMotion(self, evt):
        if evt.Dragging() and evt.LeftIsDown():
            self.lastx, self.lasty = self.x, self.y
            self.x, self.y = evt.GetPosition()

            self.xangle += (self.y - self.lasty)
            self.yangle += (self.x - self.lastx)
            self.Refresh(False)

    def createModel(self):
        self.xangle = 0
        self.yangle = 0
        self.SetCurrent()

        if not self.init:
            self.setupGLContext()
            self.init =  True
        self.stl_model.create_gl_model_list()
        self.Refresh()

    def OnSize(self, event):
        if self.GetContext():
            self.SetCurrent()
            self.setupViewport()
        self.Refresh()
        event.Skip()

    def setupViewport(self):
        size = self.GetClientSize()
        glViewport(0, 0, size.width, size.height)

    def setupProjection(self):
        maxlen = self.stl_model.ex['diameter']
        size = self.GetClientSize()
        w = size.width
        h = size.height

        half = maxlen / 2
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        if w <= h:
            factor = float(h) / w
            left = -half
            right = half
            bottom = -half * factor
            top = half * factor
        else:
            factor = float(w) / h
            left  = -half * factor
            right = half * factor
            bottom = -half
            top = half
        near = 0
        far = maxlen * 4
        glOrtho(left, right, bottom, top, near, far)

    def setupGLContext(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)

        glEnable(GL_NORMALIZE)

        ambientLight = [0.2, 0.2, 0.2, 1.0]
        diffuseLight = [0.8, 0.8, 0.8, 1.0]
        specularLight = [0.5, 0.5, 0.5, 1.0]
        position = [-1.5, 1.0, -4.0, 1.0]
        position = [-15.0, 30.0, -40.0, 1.0]

        glLightfv(GL_LIGHT0, GL_AMBIENT, ambientLight)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, diffuseLight)
        glLightfv(GL_LIGHT0, GL_SPECULAR, specularLight)
        glLightfv(GL_LIGHT0, GL_POSITION, position)
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, [0.2, 0.2, 0.2, 1.0])

        mcolor = [ 0.0, 0.0, 0.4, 1.0]
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, mcolor)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)
        glPolygonMode(GL_BACK, GL_LINE)
        glColorMaterial(GL_FRONT, GL_AMBIENT_AND_DIFFUSE)
        glEnable(GL_COLOR_MATERIAL)
        glMaterial(GL_FRONT, GL_SHININESS, 50)#96)

class ControlPanel(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        self.txtFields = {}
        self.createControls()

    def createControls(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)

        # Adding the dimension panel
        dimension_sizer = self.create_dimension_sizer()
        sizer.Add(dimension_sizer, 0, wx.EXPAND|wx.ALIGN_CENTER)

        # Adding free space
        sizer.Add((10,10))

        # Adding the direction panel - combo-box
        direction_sizer = self.create_direction_sizer()
        sizer.Add(direction_sizer, 0, wx.EXPAND)

        # Adding free space
        sizer.Add((10,10))

        # Adding the slicing panel
        slicing_sizer = self.create_slicing_sizer()
        sizer.Add(slicing_sizer, 0, wx.EXPAND)

    def create_dimension_sizer(self):
        box = wx.StaticBox(self, label="Dimension")
        sizer = wx.StaticBoxSizer(box, wx.HORIZONTAL)
        items = [("X", "xsize"), ("Y", "ysize"), ("Z", "zsize")]
        flex = wx.FlexGridSizer(rows=len(items), cols=2, hgap=2, vgap=2)
        for label, key in items:
            lblCtrl = wx.StaticText(self, label=label)
            txtCtrl = wx.TextCtrl(self, size=(70, -1), style=wx.TE_READONLY)
            flex.Add(lblCtrl)
            flex.Add(txtCtrl, 0, wx.EXPAND)
            self.txtFields[key] = txtCtrl
        flex.AddGrowableCol(1, 1)
        sizer.Add(flex, 1, wx.EXPAND|wx.ALL, 2)
        return sizer

    def set_dimensions(self, dimension):
        self.txtFields['xsize'].SetValue(str(dimension['xsize']))
        self.txtFields['ysize'].SetValue(str(dimension['ysize']))
        self.txtFields['zsize'].SetValue(str(dimension['zsize']))
        #for key in dimension:
        #    self.txtFields[key].SetValue(dimension[key])

    def create_direction_sizer(self):
        box = wx.StaticBox(self, label="Direction")
        sizer = wx.StaticBoxSizer(box, wx.HORIZONTAL)
        directions = ["+X", "-X", "+Y", "-Y", "+Z", "-Z"]
        combo = wx.ComboBox(self, -1, choices=directions)
        combo.SetEditable(False)
        combo.SetSelection(0)
        sizer.Add(combo, -1, wx.EXPAND)
        return sizer

    def create_slicing_sizer(self):
        box = wx.StaticBox(self, label="Slicing")
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        items = [("Current height", "z"), ("Step", "dz"), ("Time step", "dt")]
        flex = wx.FlexGridSizer(rows=len(items), cols=2, hgap=2, vgap=2)
        for label, key in items:
            lblCtrl = wx.StaticText(self, label=label)
            txtCtrl = wx.TextCtrl(self, size=(70, -1))
            flex.Add(lblCtrl)
            flex.Add(txtCtrl, 0, wx.EXPAND)
            self.txtFields[key] = txtCtrl
        flex.AddGrowableCol(1, 1)
        sizer.Add(flex, 1, wx.EXPAND|wx.ALL, 2)
        button_one = wx.Button(self, -1, "Slice one layer")
        sizer.Add(button_one, 0, wx.EXPAND|wx.ALL)
        button_all = wx.Button(self, -1, "Start slicing")
        sizer.Add(button_all, 0, wx.EXPAND|wx.ALL)
        return sizer

class LaserSliceFrame(wx.Frame):

    def __init__(self):
        wx.Frame.__init__(self, None, -1, "Massive Dubstep", size=(800, 600))
        self.createMenuBar()
        self.statusBar = self.CreateStatusBar()
        self.createPanel()
        #self.Bind(wx.EVT_CLOSE, self.OnQuit)
        self.model = False
        self.slice = False

    def createPanel(self):
        self.leftPanel = ControlPanel(self)
        self.sp = wx.SplitterWindow(self)
        self.modelPanel = wx.Panel(self.sp, style=wx.SUNKEN_BORDER)
        self.pathPanel = wx.Panel(self.sp, style=wx.SUNKEN_BORDER)

        '''
        self.pathCanvas = PathCanvas(self.pathPanel, self.stl_model, self.slice_array)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.pathCanvas, 1, wx.EXPAND)
        self.pathPanel.SetSizer(sizer)
        '''
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(self.leftPanel, 0, wx.EXPAND)
        box.Add(self.sp, 1, wx.EXPAND)
        self.SetSizer(box)

        self.sp.Initialize(self.modelPanel)
        self.sp.SplitVertically(self.modelPanel, self.pathPanel, 300)
        self.sp.SetMinimumPaneSize(100)

    def menuData(self):
        return (("&File", ("&Open\tCtrl+o", "Open CAD file", self.OnOpen, wx.ID_OPEN),
                          ("S&lice\tCtrl+l", "Slice CAD model", self.OnSlice, -1),
                          ("&Save\tCtrl+s", "Save slice result as xml file", self.OnSave, wx.ID_SAVE),
                          ("", "", "", ""),
                         ("&Quit\tCtrl+q", "Quit", self.OnQuit, wx.ID_EXIT)),
                ("&Help", ("&About", "About this program", self.OnAbout, wx.ID_ABOUT))
                )

    def createMenu(self, menuData):
        menu = wx.Menu()
        for label, status, handler, id in menuData:
            if not label:
                menu.AppendSeparator()
                continue
            menuItem = menu.Append(id, label, status)
            self.Bind(wx.EVT_MENU, handler, menuItem)
        return menu

    def createMenuBar(self):
        menubar = wx.MenuBar()
        for data in self.menuData():
            label = data[0]
            items = data[1:]
            menubar.Append(self.createMenu(items), label)
        self.SetMenuBar(menubar)

    def OnOpen(self, event):
        wildcard = "CAD std files (*.stl)|*.stl|All files (*.*)|*.*"
        dlg = wx.FileDialog(None, "Open CAD stl file", os.getcwd(), "", wildcard, wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.statusBar.SetStatusText(path)
            try:
                del(self.modelCanvas)
                del(self.stl_model)
            except:
                pass
            print 'open', path
            try:
                if not self.model:
                    self.stl_model = stl_utils.StlModel(path)
            except stl_utils.FormatSTLError:
                wx.MessageBox("Cannot open " + path, 'Error')
            else:
                sizer = wx.BoxSizer(wx.HORIZONTAL)
                self.modelCanvas = ModelCanvas(self.modelPanel, self.stl_model)
                sizer.Add(self.modelCanvas, wx.ID_ANY, wx.EXPAND)
                self.modelPanel.SetSizer(sizer)
                self.modelCanvas.createModel()
                self.leftPanel.set_dimensions(self.stl_model.ex)
                basename = os.path.basename(path)
                (root, ext) = os.path.splitext(basename)
                self.cadname = root
        dlg.Destroy()
        self.Refresh()


    def OnSlice(self, event):
        if not self.stl_model.loaded:
            wx.MessageBox("load a CAD model first", "warning")
            return

        slice = slice_utils.Slice(self.stl_model, float(self.leftPanel.txtFields['z'].GetValue()))
        self.pathCanvas = PathCanvas(self.pathPanel, slice.get_loops())
        self.stl_model.sliced = True
        self.pathCanvas.Refresh()
        '''
        dlg = ParaDialog(self, self.sliceParameter)
        result = dlg.ShowModal()
        if result == wx.ID_OK:
            dlg.getValues()
            self.stl_model.queue = Queue.Queue()
            thread.start_new_thread(self.cadmodel.slice, (self.sliceParameter,))
            noLayers = self.cadmodel.queue.get()
            if noLayers > 0:
                pdlg = wx.ProgressDialog("Slicing in progress", "Progress", noLayers,
                                          style=wx.PD_ELAPSED_TIME|wx.PD_REMAINING_TIME|wx.PD_AUTO_HIDE|wx.PD_APP_MODAL)

                while True:
                    count = self.cadmodel.queue.get()
                    if count == 'done':
                        count = noLayers
                        pdlg.Update(count)
                        break
                    else:
                        pdlg.Update(count)
                pdlg.Destroy()

            self.modelCanvas.createModel()
            self.leftPanel.setDimension(self.cadmodel.dimension)
            self.leftPanel.setSliceInfo(self.sliceParameter)
            self.pathCanvas.Refresh()

            if self.cadmodel.sliced:
                self.leftPanel.setNoLayer(len(self.cadmodel.layers))
                self.leftPanel.setCurrLayer(self.cadmodel.currLayer + 1)
            else:
                wx.MessageBox("no layers", "Warning")

        dlg.Destroy()
        '''



    def OnQuit(self, event):
        pass
#        exit(0)
        #self.Close(True)

    def OnSave(self, event):
        if not self.stl_model.sliced:
            return

        wildcard = "xml file (*.xml)|*.xml|All files (*.*)|*.*"
        dlg = wx.FileDialog(None, "Save slice data as xml file", os.getcwd(), self.cadname, wildcard, wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            root, ext = os.path.splitext(filename)
            if ext.lower() != '.xml':
                filename = filename + '.xml'
            self.stl_model.save(filename)
            print 'slicing info is saved in', filename

    def OnAbout(self, event):
        info = wx.AboutDialogInfo()
        info.Name = "Laser Slice"
        info.Version = "0.01"
        info.Description = "Slice stl CAD model"
        info.License = "GPL2"
        wx.AboutBox(info)



class LaserSliceApp(wx.App):

    def __init__(self, redirect=False, filename=None):
        wx.App.__init__(self, redirect, filename)

    def OnInit(self):
        self.frame = LaserSliceFrame()
        self.frame.Show()
        return True

if __name__ == '__main__':
    app = LaserSliceApp()
    app.MainLoop()