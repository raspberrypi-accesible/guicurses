import sys
import time
import curses
import widgets

class Window(object):

	def exit(self,*a,**kw):
		try:
			curses.echo(1)
			self.screen.keypad(0)
			self.screen.nodelay(0)
			curses.nocbreak()
		except Exception,e:
			print "error"
		sys.exit()

	quit=exit

	def __init__(self, screen):
		self.handlers=[self]
		self.keys = {}
		self.statusbar=1
		self.lastMessage=""
		self.daemon=1
		self.windows=[]
		self.windowVars={}
		self.windex=0
		self.screen = screen
		self.screen.nodelay(1)
		self.screen.keypad(1)
		curses.raw(1)
		curses.noecho()
		curses.cbreak()
		self.initVars()

	def initVars(self):
		self.maxy,self.maxx=self.screen.getmaxyx()
		self.curPos=[0,0]
		self.status=self.maxy-1
		self.entry=self.status-1
		self.maxy=self.entry-1
		self.screenPos=0
		self.screenPosX=0
		self.screenNum=0

	def setStatus(self,txt,*l):
		if not self.statusbar: return
		if isinstance(txt,list): txt=",".join([str(i).strip() for i in txt])
		if l: txt+=" "+" ".join(l)
		if not isinstance(txt,str): txt=str(txt)
		txt=txt.encode('utf-8')
		cur=self.screen.getyx()
		self.screen.move(self.status,0)
		self.screen.clrtoeol()
		s=txt[:self.maxx-1]
		try:
			self.screen.addstr(self.status,0,s)
		except:
			generate_error_report()
			self.setStatus("error")
		self.screen.move(cur[0],cur[1])
		self.screen.refresh()

		self.screen.refresh()


	def run(self):
		while 1:
			time.sleep(0.01)
			c=self.screen.getch()
			if c!=-1:
				for handler in self.handlers[:]:
					if handler.handleKey(c):
						self.check_changes(handler)
						break

	def check_changes(self, handler):
		if hasattr(handler, "selected_action"):
			self.handlers.remove(handler)
			getattr(self, handler.selected_action)(handler.dir)
		elif not hasattr(handler, "controls"): return
		for control in handler.controls:
			if control.selected == 1 or control.done == 1:
				self.handlers.remove(handler)
				if "." in control.action:
					self.open_file(control.action)
				else:
					getattr(self, control.action)()

	def handleKey(self,k,*args):
		pass
#		if k in self.keys:
#			try:
#				exec(self.keys[k])
#				return 1
#			except Exception,e:
#				self.setStatus("KeyboardError:%s" % (e,))
#		return None

	def parse_menu(self, items, is_submenu=False):
		controls = []
		for i in items:
			if len(i) > 2:
				controls.append((widgets.Button, dict(prompt=i[1], action=i[0], help_string=i[2])))
			else:
				controls.append((widgets.Button, dict(prompt=i[1], action=i[0])))
		if is_submenu:
			controls.append((widgets.Button, "Back"))
		return controls