import curses
from guicurses  import widgets, window

class mainWindow(window.Window):

	def __init__(self, *args, **kwargs):
		super(mainWindow, self).__init__(*args, **kwargs)
		self.run()

	def run(self):
		while 1:
			c = self.screen.getch()
			if c != -1:
				self.setStatus(c)

curses.wrapper(mainWindow)
