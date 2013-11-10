import wx
import stl_utils
import slice_utils

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

'''
def convertXToOpenGL(x):
    return 50 * (x + 175) / 300


def convertYToOpenGL(y):
    return 50 * (y - 67) / 300
'''

def convertXToOpenGL(x):
    return (x) / 200


def convertYToOpenGL(y):
    return (y) / 200

MODEL_LIST_ID = 1000
SLICE_LIST_ID = 1001
#SLICE_METHOD = 'fully_scan_old'
SLICE_METHOD = 'fully_scan'
#SLICE_METHOD = 'loops'
#SLICE_METHOD = 'shape'

#almost kill program if something wrong
ASRT = True

class SliceCanvas(glcanvas.GLCanvas):

    def __init__(self, parent):
        glcanvas.GLCanvas.__init__(self, parent, -1, size=parent.Size)
        self.parent = parent
        self.slice = None
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.onEraseBackground)
        self.Bind(wx.EVT_SIZE, self.onSize)
        self.Bind(wx.EVT_PAINT, self.onPaint)
        self.Refresh()

    def clear(self):
        self.SetCurrent()
        glClear(GL_COLOR_BUFFER_BIT)
        self.SwapBuffers()

    def onEraseBackground(self, event):
        pass # Do nothing, to avoid flashing on MSW.

    def set_slice(self, slice):
        self.onPaint()
        self.slice = slice
        if SLICE_METHOD == 'fully_scan_old':
            lines = self.slice.fully_scan_old()
            glNewList(SLICE_LIST_ID, GL_COMPILE)
            glBegin(GL_LINES)
            glColor3d(1, 1, 1)
            for line in lines:
                for p in line:
                    glVertex(convertXToOpenGL(p.x), convertYToOpenGL(p.y))
            glEnd()
            glEndList()
        elif SLICE_METHOD == 'fully_scan':
            lines = self.slice.fully_scan()
            glNewList(SLICE_LIST_ID, GL_COMPILE)
            glBegin(GL_LINES)
            glColor3d(1, 1, 1)
            for line in lines:
                for p in line:
                    glVertex(convertXToOpenGL(p.x), convertYToOpenGL(p.y))
            glEnd()
            glEndList()
        elif SLICE_METHOD == 'shape':
            lines = self.slice.get_shape()
            glNewList(SLICE_LIST_ID, GL_COMPILE)
            glBegin(GL_LINES)
            glColor3d(1, 1, 1)
            i = 0.0
            for line in lines:
                for p in line:
                    glColor3d(i / len(lines), i / len(lines), 1)
                    glVertex(convertXToOpenGL(p.x), convertYToOpenGL(p.y))
                i += 1.0
            glEnd()
            glEndList()
        elif SLICE_METHOD == 'loops':
            loops = self.slice.get_loops()
            glNewList(SLICE_LIST_ID, GL_COMPILE)
            for loop in loops:
                glBegin(GL_LINE_LOOP)
                i = 0.0
                for p in loop:
                    glColor3d(i / len(loop), i / len(loop), 1)
                    glVertex(convertXToOpenGL(p.x), convertYToOpenGL(p.y))
                    i += 1.0
                glEnd()
            glEndList()
        else:
            print "unsupposed slice method"
            assert 0
        self.Refresh()

    def onSize(self, event):
        if self.GetContext():
            self.SetCurrent()
            self.Size = self.parent.Size
            size = self.GetClientSize()
            glViewport(0, 0, size.width, size.height)
        self.Refresh()
        event.Skip()

    def clear(self):
        self.slice = None
        self.SwapBuffers()

    def onPaint(self, event=None):
        try:
            wx.PaintDC(self)
        except:
            pass
        if self.slice:
            self.SetCurrent()
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glCallList(SLICE_LIST_ID)
            self.SwapBuffers()
        else:
            self.SwapBuffers()


class ModelCanvas(glcanvas.GLCanvas):

    def __init__(self, parent):
        glcanvas.GLCanvas.__init__(self, parent, -1, size=parent.Size)
        self.parent = parent
        self.model = None
        self.ex = None
        self.direction = ''
        self.lastx = self.x = 30
        self.lasty = self.y = 30
        self.xangle = 0
        self.yangle = 0

        self.Bind(wx.EVT_ERASE_BACKGROUND, self.onEraseBackground)
        self.Bind(wx.EVT_SIZE, self.onSize)
        self.Bind(wx.EVT_PAINT, self.onPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.onMouseDown)
        self.Bind(wx.EVT_LEFT_UP, self.onMouseUp)
        self.Bind(wx.EVT_MOTION, self.onMouseMotion)


    def set_model(self, model):
        self.model = model
        self.ex = model.ex.copy()
        self.ex = model.ex
        self.direction = model.direction

        glNewList(MODEL_LIST_ID, GL_COMPILE)
        glColor(1, 0, 0)
        glBegin(GL_TRIANGLES)
        for facet in self.model.facets:
            normal = facet.normal
            glNormal3f(normal.x, normal.y, normal.z)
            for p in facet:
                glVertex3f(p.x, p.y, p.z)
        glEnd()
        glEndList()

        self.Refresh()
        self.onPaint()

    def onEraseBackground(self, event):
        pass # Do nothing, to avoid flashing on MSW.

    def onPaint(self, event=None):
        try:
            wx.PaintDC(self)
        except:
            print 'error in wx.PaintDC(self) - ModelCanvas'
            pass
        if self.model:
            self.SetCurrent()
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            self.setup_glcontext()
            self.setup_projection()
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            glTranslatef(0, 0, -self.model.ex['diameter'])
            # Rotate model
            glRotatef(self.xangle, 1, 0, 0)
            glRotatef(self.yangle, 0, 1, 0)

            # Move model to origin
            if self.direction == "+Z":
                glTranslatef(-self.ex['xcenter'], -self.ex['ycenter'], -self.ex['zcenter'])
            elif self.direction == "-Z":
                glTranslatef(-self.ex['xcenter'], -self.ex['ycenter'], self.ex['zcenter'])
            elif self.direction == "+Y":
                glTranslatef(-self.ex['zcenter'], -self.ex['xcenter'], -self.ex['ycenter'])
            elif self.direction == "-Y":
                glTranslatef(-self.ex['zcenter'], self.ex['xcenter'], -self.ex['ycenter'])
            elif self.direction == "+X":
                glTranslatef(-self.ex['ycenter'], -self.ex['zcenter'], -self.ex['xcenter'])
            elif self.direction == "-X":
                glTranslatef(self.ex['ycenter'], -self.ex['zcenter'], -self.ex['xcenter'])

            glCallList(MODEL_LIST_ID)
            self.SwapBuffers()
        else:
            self.SetCurrent()
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            self.SwapBuffers()


#    def showPath(self):
#        if self.stl_model.sliced:
#            layerId = self.stl_model.createGLLayerList()
#            glCallList(layerId)

    def onMouseDown(self, event):
        self.CaptureMouse()
        self.x, self.y = self.lastx, self.lasty = event.GetPosition()

    def onMouseUp(self, event):
        if self.HasCapture():
            self.ReleaseMouse()

    def onMouseMotion(self, event):
        if event.Dragging() and event.LeftIsDown():
            self.lastx, self.lasty = self.x, self.y
            self.x, self.y = event.GetPosition()

            self.xangle += (self.y - self.lasty)
            self.yangle += (self.x - self.lastx)
            self.Refresh(False)

    def onSize(self, event):
        if self.GetContext():
            self.SetCurrent()
            self.Size = self.parent.Size
            self.setup_viewport()
        self.Refresh()
        event.Skip()

    def setup_viewport(self):
        size = self.GetClientSize()
        glViewport(0, 0, size.width, size.height)

    def setup_projection(self):
        maxlen = self.model.ex['diameter']
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

    def setup_glcontext(self):
        glEnable(GL_NORMALIZE)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)

        ambientLight = [0.2, 0.2, 0.2, 1.0]
        diffuseLight = [0.8, 0.8, 0.8, 1.0]
        specularLight = [0.5, 0.5, 0.5, 1.0]
        position = [2500.0, -3000.0, 4000.0, 1.0]
        #position = [-15.0, 30.0, -40.0, 1.0]

        glLightfv(GL_LIGHT0, GL_AMBIENT, ambientLight)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, diffuseLight)
        glLightfv(GL_LIGHT0, GL_SPECULAR, specularLight)
        glLightfv(GL_LIGHT0, GL_POSITION, position)
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, [0.2, 0.2, 0.2, 1.0])

        mcolor = [0.0, 0.0, 0.4, 1.0]
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
        self.parent = parent
        self.txt_fields = {}
        self.buttons = {}
        self.combo = None
        self.create_controls()

    def create_controls(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)

        # Adding the dimension panel
        dimension_sizer = self.create_dimension_sizer()
        sizer.Add(dimension_sizer, 0, wx.EXPAND | wx.ALIGN_CENTER)

        # Adding free space
        sizer.Add((10,10))

        # Adding the direction panel - combo-box
        direction_sizer = self.create_direction_sizer()
        sizer.Add(direction_sizer, 0, wx.EXPAND)

        # Adding free space
        sizer.Add((10,10))

        # Adding the zoom panel
        zoom_sizer = self.create_zoom_sizer()
        sizer.Add(zoom_sizer, 0, wx.EXPAND)

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
            self.txt_fields[key] = txtCtrl
        flex.AddGrowableCol(1, 1)
        sizer.Add(flex, 1, wx.EXPAND|wx.ALL, 2)
        return sizer

    def set_dimensions(self, dimension):
        self.txt_fields['xsize'].SetValue(str(dimension['xsize']))
        self.txt_fields['ysize'].SetValue(str(dimension['ysize']))
        self.txt_fields['zsize'].SetValue(str(dimension['zsize']))

    def create_zoom_sizer(self):
        box = wx.StaticBox(self, label="Zoom in ... times")
        sizer = wx.StaticBoxSizer(box, wx.HORIZONTAL)

        zoom_value = wx.TextCtrl(self, size=(70, -1))
        button_apply = wx.Button(self, -1, "Apply")
        button_apply.Bind(wx.EVT_BUTTON, self.parent.onZoom)
        self.buttons['apply'] = button_apply
        self.txt_fields['zoom_value'] = zoom_value
        sizer.Add(zoom_value)
        sizer.Add(button_apply)
        return sizer

    def create_direction_sizer(self):
        box = wx.StaticBox(self, label="Direction")
        sizer = wx.StaticBoxSizer(box, wx.HORIZONTAL)
        directions = ["+X", "-X", "+Y", "-Y", "+Z", "-Z"]
        combo = wx.ComboBox(self, -1, choices=directions)
        combo.SetEditable(False)
        # Choose direction = "+Z"
        combo.SetSelection(4)
        combo.Bind(wx.EVT_COMBOBOX, self.parent.onCombo)
        self.combo = combo
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
            self.txt_fields[key] = txtCtrl
        flex.AddGrowableCol(1, 1)
        sizer.Add(flex, 1, wx.EXPAND|wx.ALL, 2)
        button_one = wx.Button(self, -1, "Slice one layer")
        button_one.Bind(wx.EVT_BUTTON, self.parent.onSlice)
        self.buttons['one'] = button_one
        sizer.Add(button_one, 0, wx.EXPAND|wx.ALL)
        button_all = wx.Button(self, -1, "Start slicing")
        button_all.Bind(wx.EVT_BUTTON, self.parent.onStartSlicing)
        self.buttons['all'] = button_all
        sizer.Add(button_all, 0, wx.EXPAND|wx.ALL)
        return sizer


class MainFrame(wx.Frame):

    def __init__(self):
        self.model = None
        wx.Frame.__init__(self, None, -1, "Massive Dubstep", size=(800, 600))
        self.create_menu_bar()
        self.status_bar = self.CreateStatusBar()
        self.left_panel = ControlPanel(self)
        self.sp = wx.SplitterWindow(self, -1)
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(self.left_panel, 0, wx.EXPAND)
        box.Add(self.sp, 1, wx.EXPAND)
        self.SetSizer(box)

        self.model_panel = wx.Panel(self.sp, -1, style=wx.SUNKEN_BORDER)
        self.slice_panel = wx.Panel(self.sp, -1, style=wx.SUNKEN_BORDER)
        self.sp.Initialize(self.model_panel)
        self.sp.SplitVertically(self.model_panel, self.slice_panel, 300)
        self.sp.SetMinimumPaneSize(100)

        self.model_canvas = ModelCanvas(self.model_panel)
        model_sizer = wx.BoxSizer(wx.HORIZONTAL)
        model_sizer.Add(self.model_canvas, 0, wx.EXPAND)
        self.model_panel.SetSizer(model_sizer)

        self.slice_canvas = SliceCanvas(self.slice_panel)
        slice_sizer = wx.BoxSizer(wx.HORIZONTAL)
        slice_sizer.Add(self.slice_canvas, 0, wx.EXPAND)
        self.slice_panel.SetSizer(slice_sizer)


        self.timer = wx.Timer(self, -1)
        self.Bind(wx.EVT_TIMER, self.onTickSlicing, self.timer)

        self.z = 0

        self.Bind(wx.EVT_CLOSE, self.onQuit)
        self.projector_frame = ProjectorFrame(self)


    def menu_data(self):
        return (("&File", ("&Open\tCtrl+o", "Open CAD file", self.onOpen, wx.ID_OPEN),
                          ("", "", "", ""),
                          ("&Quit\tCtrl+q", "Quit", self.onQuit, wx.ID_EXIT)
                ),
                ("&Help", ("&About", "About this program", self.onAbout, wx.ID_ABOUT))
               )

    def create_menu(self, menu_data):
        menu = wx.Menu()
        for label, status, handler, id in menu_data:
            if not label:
                menu.AppendSeparator()
                continue
            menu_item = menu.Append(id, label, status)
            self.Bind(wx.EVT_MENU, handler, menu_item)
        return menu

    def create_menu_bar(self):
        menu_bar = wx.MenuBar()
        for data in self.menu_data():
            label = data[0]
            items = data[1:]
            menu_bar.Append(self.create_menu(items), label)
        self.SetMenuBar(menu_bar)

    def set_model(self, model):
        self.model = model
        self.left_panel.set_dimensions(model.ex)
        #self.model.changeDirection(self.left_panel.combo.Value)
        self.model_canvas.set_model(model)
        print "There are %d facets in the model" % len(self.model.facets)

    def set_slice(self, z):
        try:
            slice = slice_utils.Slice(self.model, z, ASRT)
            self.slice_canvas.set_slice(slice)
            # Check if project_frame exist before setting the slice
            if self.projector_frame:
                self.projector_frame.canvas.set_slice(slice)
        except slice_utils.SizeSliceError:
            wx.MessageBox("Cant slice so big model. The max size is 400 mm", 'Error')
        except:
            print 'failed in slice'
            self.stop_timer()

    def stop_timer(self):
        self.timer.Stop()
        self.left_panel.buttons['all'].SetLabel("Start slicing")

    def onOpen(self, event):
        wildcard = "CAD std files (*.stl)|*.stl|All files (*.*)|*.*"
        dlg = wx.FileDialog(None, "Open CAD stl file", os.getcwd(), "", wildcard, wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.status_bar.SetStatusText(path)
            try:
                model = stl_utils.StlModel(path)
                model.centering()
            except:
                wx.MessageBox("Cannot open " + path, 'Error')
            else:
                self.slice_canvas.clear()
                self.set_model(model)
                self.left_panel.txt_fields["z"].SetLabel("%.2f" % 0.01)
                self.left_panel.txt_fields["dz"].SetLabel("%.2f" % 5)
                self.left_panel.txt_fields["dt"].SetLabel("%d" % 200)
                self.left_panel.txt_fields["zoom_value"].SetLabel("%d" % 1)

        dlg.Destroy()
        self.Refresh()

    def onZoom(self, event):
        zoom = float(self.left_panel.txt_fields['zoom_value'].Value)
        self.model.zoom(zoom)
        self.left_panel.set_dimensions(self.model.ex)
        z = float(self.left_panel.txt_fields["z"].Value)
        z *= zoom
        self.z = z
        self.left_panel.txt_fields["z"].SetLabel("%.2f" % self.z)
        self.set_slice(z + self.model.ex['minz'])

    def onSlice(self, event):
        if self.model is None:
            wx.MessageBox("load a CAD model first", "warning")
        else:
            z = float(self.left_panel.txt_fields["z"].Value)
            print "Slicing %.2f" % self.z
            self.set_slice(z + self.model.ex['minz'])

    def onStartSlicing(self, event):
        if self.model is None:
            wx.MessageBox("load a CAD model first", "warning")
        elif self.timer.IsRunning():
            self.timer.Stop()
            print "slicing stopped!"
            self.left_panel.buttons['all'].SetLabel("Start slicing")
        else:
            print "starting slicing..."
            self.z = float(self.left_panel.txt_fields["z"].Value)
            self.timer.Start(float(self.left_panel.txt_fields["dt"].Value))
            self.left_panel.buttons['all'].SetLabel("Stop slicing")

    def onTickSlicing(self, event):
        self.z += float(self.left_panel.txt_fields["dz"].Value)
        self.left_panel.txt_fields["z"].SetLabel("%.2f" % self.z)

        print "Slicing %.2f" % self.z
        self.set_slice(self.z + self.model.ex['minz'])

        if self.z + self.model.ex['minz'] > self.model.ex['maxz']:
            self.stop_timer()
            if self.projector_frame:
                self.projector_frame.canvas.clear()
            print "Finish!"

    def onCombo(self, event):
        if not self.model is None:
            self.model.changeDirection(self.left_panel.combo.Value)

    def onQuit(self, event):
        if self.projector_frame:
            self.projector_frame.Close()
        self.Destroy()

    def onAbout(self, event):
        info = wx.AboutDialogInfo()
        info.Name = "Laser Slice"
        info.Version = "0.01"
        info.Description = "Esho ne pridumali"
        wx.AboutBox(info)


class ProjectorFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, None, size=wx.DefaultSize, title='Projector Frame')
        self.SetPosition((wx.Display(1).GetGeometry()[0], 0))
        self.ShowFullScreen(True)
        self.canvas = SliceCanvas(self)
        self.canvas.clear()


class MainApp(wx.App):

    def __init__(self, redirect=False, filename=None):
        wx.App.__init__(self, redirect, filename)

    def OnInit(self):
        self.frame = MainFrame()
        self.frame.projector_frame.Show()
        self.frame.Show()
        return True

if __name__ == '__main__':
    open('sliser.log', 'w')
    app = MainApp()
    app.MainLoop()