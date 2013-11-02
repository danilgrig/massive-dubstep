from slice_utils import *
from stl_utils import *

try:
    import wx
    from wx import glcanvas
except ImportError:
    raise ImportError, "Required dependency wx.glcanvas not present"

try:
    from OpenGL.GL import *
except ImportError:
    raise ImportError, "Required dependency OpenGL not present"

def convertXToOpenGL(x):
    return x / 300

def convertYToOpenGL(x):
    return x / 300

class GLFrame(wx.Frame):
    """A simple class for using OpenGL with wxPython."""

    def __init__(self, parent, id, title, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.DEFAULT_FRAME_STYLE,
                 name='frame'):
        #
        # Forcing a specific style on the window.
        #   Should this include styles passed?
        style = wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE

        super(GLFrame, self).__init__(parent, id, title, pos, size, style, name)
        self.SetPosition((wx.Display(0).GetGeometry()[0], 0))
        self.GLinitialized = False
        attribList = (glcanvas.WX_GL_RGBA, # RGBA
                      glcanvas.WX_GL_DOUBLEBUFFER, # Double Buffered
                      glcanvas.WX_GL_DEPTH_SIZE, 24) # 24 bit

        #
        # Create the canvas
        self.canvas = glcanvas.GLCanvas(self, attribList=attribList)

        #
        # Set the event handlers.
        self.canvas.Bind(wx.EVT_ERASE_BACKGROUND, self.processEraseBackgroundEvent)
        self.canvas.Bind(wx.EVT_SIZE, self.processSizeEvent)
        self.canvas.Bind(wx.EVT_PAINT, self.processPaintEvent)

        #model = stl_utils.StlModel('pudge.stl')
        self.model = stl_utils.StlModel('stl_examples\\pencildome.stl')
        self.model.changeDirection("+Z")
        self.model.zoom(8)
   #
    # Canvas Proxy Methods

    def GetGLExtents(self):
        """Get the extents of the OpenGL canvas."""
        return self.canvas.GetClientSize()

    def SwapBuffers(self):
        """Swap the OpenGL buffers."""
        self.canvas.SwapBuffers()

    #
    # wxPython Window Handlers

    def processEraseBackgroundEvent(self, event):
        """Process the erase background event."""
        pass # Do nothing, to avoid flashing on MSWin

    def processSizeEvent(self, event):
        """Process the resize event."""
        if self.canvas.GetContext():
            # Make sure the frame is shown before calling SetCurrent.
            self.Show()
            self.canvas.SetCurrent()

            size = self.GetGLExtents()
            self.OnReshape(size.width, size.height)
            self.canvas.Refresh(False)
        event.Skip()

    def processPaintEvent(self, event):
        """Process the drawing event."""
        self.canvas.SetCurrent()

        # This is a 'perfect' time to initialize OpenGL ... only if we need to
        if not self.GLinitialized:
            self.OnInitGL()
            self.GLinitialized = True

        self.OnDraw()
        event.Skip()

    #
    # GLFrame OpenGL Event Handlers

    def OnInitGL(self):
        """Initialize OpenGL for use in the window."""
        glClearColor(0, 0, 0, 1)

    def OnReshape(self, width, height):
        """Reshape the OpenGL viewport based on the dimensions of the window."""
        glViewport(0, 0, width, height)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(-0.5, 0.5, -0.5, 0.5, -1, 1)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def draw_loops(self, slice):
        loops = slice.get_loops()
        for loop in loops[0:1]:
            glBegin(GL_POLYGON)
            #glBegin(GL_LINE_STRIP)
            if not counter_clock_wise(loop):
                glColor3d(1, 1, 1)
            else:
                glColor3d(0, 0, 0)
            for p in loop:
                glVertex(convertXToOpenGL(p.x), convertYToOpenGL(p.y))
            glEnd()
        self.SwapBuffers()
        #import time
        #time.sleep(1)

    def draw_full_scan(self, slice):
        lines = slice.fully_scan()
        glBegin(GL_LINES)
        for line in lines:
            glColor3d(1, 1, 1)
            p = line.p1
            glVertex(convertXToOpenGL(p.x), convertYToOpenGL(p.y))
            glColor3d(1, 0, 0)
            p = line.p2
            glVertex(convertXToOpenGL(p.x), convertYToOpenGL(p.y))
        glEnd()
        self.SwapBuffers()
        #import time
        #time.sleep(1)

    def draw_int_scan(self, slice):
        lines = slice.int_scan()
        glBegin(GL_LINES)
        for line in lines:
            glColor3d(1, 1, 1)
            p = line.p1
            glVertex(convertXToOpenGL(p.x), convertYToOpenGL(p.y))
            glColor3d(1, 0, 0)
            p = line.p2
            glVertex(convertXToOpenGL(p.x), convertYToOpenGL(p.y))
        glEnd()
        self.SwapBuffers()
        #import time
        #time.sleep(1)

    def OnDraw(self, *args, **kwargs):
        try:
            slice = Slice(self.model, 240)
            glClear(GL_COLOR_BUFFER_BIT)
            self.draw_int_scan(slice)
            #self.draw_full_scan(slice)
        except SizeSliceError:
            print "Cant slice model"
            exit(0)
        except FormatSTLError:
            print "Cant read model"
            exit(0)
        except IOError:
            print ".stl file doesnt exist"
            exit(0)


app = wx.PySimpleApp()
frame = GLFrame(None, -1, 'GL Window')
frame.ShowFullScreen(True, style=wx.FULLSCREEN_ALL)

app.MainLoop()
app.Destroy()