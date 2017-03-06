#holds basic GUI structures for use in curses (Dialog, button, editBox, readline, listbox and fileBrowser)
# Taken and modified from http://bmcginty.us/clifox.git
import curses, time, os, os.path, string, sys
from curses import ascii

class GuiObject(object):
	done = 0

	def beepIfNeeded(self):
#		if self.base.config.beeps:
		curses.beep()

	def setStatus(self,*a,**kw):
		return self.base.setStatus(*a,**kw)

	def onFocus(self, *args, **kwargs): self.screen.move(self.y, self.x)

class Dialog(GuiObject):
	"""control holder
down and up arrows move through controls
enter selects default button or displays error if not one
"""
	@property
	def controlIndex(self):
		return self._controlIndex

	@controlIndex.setter
	def controlIndex(self, i):
		self._controlIndex  =  i
		self.controls[self._controlIndex].onFocus()
		return i

	def __init__(self, screen = None, base = None, y = 0, x = 0, title="", controls = [], can_go_back=True):
		self.base = base
		self.screen = screen
		self.y, self.x = y, x
		self._controls = controls
		self.controls = []
		self.can_go_back = can_go_back
		self.title = title
		self.initialDraw()
		self.draw()

	def initialDraw(self):
		for i in range(0, len(self._controls)):
			co = self._controls[i]
			c = co[0](screen=self.screen, base=self.base, y=i+1, can_go_back=self.can_go_back, **co[1])
			self.controls.append(c)
		self.controlIndex = 0
		self.screen.move(self.y, 0)
		self.screen.clrtoeol()
		self.screen.addstr(self.y, 0, self.title)

	def draw(self):
		for i in self.controls:
			i.draw()

	def handleKey(self, c):
		ret = 1
		if c == curses.KEY_DOWN:
			if self.controlIndex >= len(self.controls) -1:
				self.beepIfNeeded()
				self.setStatus("No more controls in this dialog. Please up arrow to the first control.")
				self.controlIndex = len(self.controls) -1
			else:
				self.controlIndex += 1
		elif c == curses.KEY_UP:
			if self.controlIndex <= 0:
				self.beepIfNeeded()
				self.setStatus("This is the first control in this dialog.")
				self.controlIndex = 0
			else:
				self.controlIndex -= 1
		else:
			ret = self.controls[self.controlIndex].handleKey(c)
		return ret

class Button(GuiObject):
	def __init__(self, screen=None, base=None, y=1, x=0, can_go_back=True, prompt="Button", action="", help_string=""):
		self.base = base
		self.screen = screen
		self.y, self.x = y, x
		self.prompt = prompt
		self.selected = 0
		self.draw()
		self.action  =  action
		self.help_string = help_string
		self.can_go_back = can_go_back

	def draw(self):
		s =  self.prompt
		self.screen.addstr(self.y, self.x, s)
		self.screen.refresh()

	def handleKey(self, k):
		if k == 10 or k == curses.KEY_RIGHT: # Enter key or right for easier use
			self.done = 1
			self.selected = 1
			return 1
		elif k == curses.KEY_F1:
			if hasattr(self, "help_string"):
				self.setStatus(self.help_string)
				return 1
		elif k == curses.KEY_BACKSPACE or k == curses.KEY_LEFT and self.can_go_back: # Let's go back
			self.base.go_back()
			return 1
		return None

class comboBox(GuiObject):

	def __init__(self, screen=None, base=None, y=1, x=0, options=[], default=None, help_string="", *args, **kwargs):
		self.base = base
		self.screen = screen
		self.y, self.x = y, x
		self.help_string = help_string
		if default == None:
			self.default = 0
		else:
			self.default = default
		self.options = options
		self.prompt = self.options[default][1]
		self.selected_value = self.options[default][0]
		self.selected = 0
		self.draw()

	def draw(self):
		s =  " "+self.prompt
		self.screen.move(self.y, 0)
		self.screen.clrtoeol()

		self.screen.addstr(self.y, self.x, s)
		self.screen.refresh()

	def handleKey(self, k):
		if k == 10 or k == curses.KEY_RIGHT: # Enter key or right for easier use
			self.change_value(1)
			return 1
		elif k == curses.KEY_F1:
			if hasattr(self, "help_string"):
				self.setStatus(self.help_string)
				return 1
		elif k == curses.KEY_LEFT:
			self.change_value(-1)
			return 1
		return None

	def change_value(self, number):
		if number == 1:
			if self.default < len(self.options)-1:
				self.default += 1
				self.prompt = self.options[self.default][1]
				self.draw()
				self.selected_value = self.options[self.default][0]
		elif number == -1:
			if self.default > 0:
				self.default -= 1
				self.prompt = self.options[self.default][1]
				self.draw()
				self.selected_value = self.options[self.default][0]

class Editbox(object):
	"""Editing widget using the interior of a window object.
		Supports the following Emacs-like key bindings:
 Ctrl-A Go to left edge of window.
 Ctrl-B Cursor left, wrapping to previous line if appropriate.
 Ctrl-D Delete character under cursor.
 Ctrl-E Go to right edge (stripspaces off) or end of line (stripspaces on).
 Ctrl-F Cursor right, wrapping to next line when appropriate.
 Ctrl-G Terminate, returning the window contents.
 Ctrl-H Delete character backward.
 Ctrl-J Terminate if the window is 1 line, otherwise insert newline.
 Ctrl-K If line is blank, delete it, otherwise clear to end of line.
 Ctrl-L Refresh screen.
 Ctrl-N Cursor down; move down one line.
 Ctrl-O Insert a blank line at cursor location.
 Ctrl-P Cursor up; move up one line.
 Move operations do nothing if the cursor is at an edge where the movement is not possible.
The following synonyms are supported where possible:
 KEY_LEFT  =  Ctrl-B, KEY_RIGHT  =  Ctrl-F, KEY_UP  =  Ctrl-P, KEY_DOWN  =  Ctrl-N, KEY_BACKSPACE  =  Ctrl-h
 """
	def __init__(self, screen=None, base=None, y=1, x=0, default="edit field"):
		self.base = base
		self.value = default
		self.win = screen
		self.loop = self.edit
		(self.maxy, self.maxx)  =  self.win.getmaxyx()
		self.maxy -=  2
		self.maxx -=  1
		self.stripspaces  =  1
		self.lastcmd  =  None
		self.text  =  [[] for y in xrange(self.maxy+1)]
		self.win.keypad(1)
		self.win.move(0,0)

	def text_insert(self, y, x, ch):
		if len(self.text[y]) > x:
			self.text[y].insert(x, ch)
		else: # < =  x
#			self.text[y] + =  [curses.ascii.SP] * (x - len(self.text[y]))
			self.text[y].append(ch)

	def text_delete(self, y, x):
		if y < 0 or x < 0 or y >= len(self.text) or x >=  len(self.text[y]): return
		del self.text[y][x]
 
	def _end_of_line(self, y):
		"""Go to the location of the first blank on the given line."""
		last  =  self.maxx
		while 1:
			if curses.ascii.ascii(self.win.inch(y, last)) != curses.ascii.SP:
				last  =  min(self.maxx, last+1)
				break
			elif last == 0:
				break
			last  = last - 1
		return last

	def do_command(self, ch):
		"Process a single editing command."
		(y, x)  =  self.win.getyx()
		self.lastcmd  =  ch
		if ch == curses.ascii.SOH:									# ^a
			x = 0
			self.win.move(y, x)
		elif ch in (curses.ascii.STX,curses.KEY_LEFT, curses.ascii.BS, curses.KEY_BACKSPACE,127):
			if x > 0:
				x -= 1
				self.win.move(y, x)
			elif y  == 0:
				pass
			else:
				y -= 1
				x = len(self.text[y])-1 #if len(self.text[y])<self.maxx else self.maxx
				self.win.move(y, x)
			if ch in (curses.ascii.BS, curses.KEY_BACKSPACE, 127):
				self.win.delch()
				y, x  =  self.win.getyx()
				self.text_delete(y, x)
		elif ch in (curses.ascii.EOT, curses.KEY_DC):									# ^d
			self.win.delch()
			self.text_delete(y, x)
		elif ch  ==  curses.ascii.ENQ:									# ^e
			x  =  len(self.text[y]) if len(self.text[y])<self.maxx else self.maxx
			self.win.move(y, x)
		elif ch in (curses.ascii.ACK, curses.KEY_RIGHT):				# ^f
			if x < self.maxx and x < len(self.text[y]):
				x += 1
				self.win.move(y, x)
			elif y == self.maxy:
				pass
			else:
				y += 1
				x = 0
				self.win.move(y, x)
		elif ch == curses.ascii.BEL:									# ^g
			return True
		elif ch in (10, 13):				# ^j ^m
			if y < self.maxy:
				y += 1
				x = 0
				self.win.move(y, x)
		elif ch  ==  curses.ascii.VT:							# ^k
			if x < len(self.text[y]):
				self.win.clrtoeol()
				del self.text[y][x:]
			else:
				self.win.deleteln()
				del self.text[y]
#			self.win.move(y, x)
		elif ch  ==  curses.ascii.FF:							# ^l
			self.win.refresh()
		elif ch in (curses.ascii.SO, curses.KEY_DOWN):			# ^n
			if y < self.maxy:
				y += 1
				x = len(self.text[y]) if x > len(self.text[y]) else x
				self.win.move(y, x)
			else:
				pass
		elif ch  ==  curses.ascii.SI:							# ^o
			self.win.insertln()
			self.text.insert(y, [])
		elif ch in (curses.ascii.DLE, curses.KEY_UP):				# ^p
			if y > 0:
				y -= 1
				x = len(self.text[y]) if x > len(self.text[y]) else x
				self.win.move(y, x)
			else:
				pass
		elif ch  ==  curses.KEY_HOME:
			y = 0
			x = len(self.text[y]) if x > len(self.text[y]) else x
			self.win.move(y, x)
		elif ch  ==  curses.KEY_END:
			y = len(self.text)
#			x = len(self.text[y]) if x > len(self.text[y]) else x
			self.win.move(y,x)
		elif ch == curses.KEY_F2:
			if self.externalEdit()  ==  None:
				self.setStatus("No external editor found.")
			else:
				return True				
		elif ch>31 and ch<256:
			ch  =  self.getunicode(ch)
			if y < self.maxy or x < self.maxx:
				self.text_insert(y, x, ch)
				self.win.addstr(y, 0, ''.join(self.text[y]))
				if x<self.maxx:
					x += 1
				else:
					x = 0
					y += 1
				self.win.move(y, x)
		self.draw()
		return False

	def gather(self):
		tmp  =  [''] * len(self.text)
		for y in xrange(len(self.text)):
			tmp[y]  =  ''.join(self.text[y])
			tmp[y]  =  tmp[y].rstrip()
		return '\n'.join(tmp).strip()

	def clear(self):
		self.text  =  [[] for y in xrange(self.maxy+1)]
		for y in xrange(self.maxy+1):
			self.win.move(y, 0)
			self.win.clrtoeol()
		self.win.move(0, 0)
 
	def draw(self):
		y, x = self.win.getyx()
		l  =  len(self.text)
		if l < self.maxy:
			for i in range(l):
				self.win.move(i, 0)
				self.win.clrtoeol()
				self.win.addstr(i, 0, ''.join(self.text[i]))
			self.win.move(y, x)
		else:
			for i in xrange(l-self.maxy):
				self.win.move(i, 0)
				self.win.clrtoeol()
				self.win.addstr(i, 0, ''.join(self.text[i]))
			self.win.move(y, x)
		self.win.refresh()

	def externalEdit(self):
#		if self.base.config.editor:
#			e = self.base.config.editor
		if os.environment.get("nano"):
			e = os.environment.get("EDITOR")
		else:
			return None
		tempfile = "/tmp/squigglitz"
		open(tempfile,"wb").write(self.gather())
		cmd = "%s %s" % (e,tempfile)
		os.system(cmd)
		fh = open(tempfile,"rb")
		self.text = fh.readlines()
		fh.close()
		os.remove(tempfile)
		return self.text
 
	def getunicode(self, c):
		tc  =  u' '
		buf  =  ''
		done  =  False
		nc  =  chr(c)
		buf += nc
		if ord(nc) in (194, 195):
			nc  =  chr(self.win.getch())
			buf += nc
		try:
			tc  =  buf.decode()
			done  =  True
		except:
			pass
		return tc

	def edit(self):
		self.win.clear()
		text = list(self.value)
		while 1:
			if text != None and len(text)>0:
				ch = ord(text.pop(0))
				if len(text) == 0:
					text = -1
			else:
				ch  =  self.win.getch()
				if ch == -1:
					time.sleep(0.02)
					continue
			o_ch  =  ch
			if self.do_command(ch):
				break
			if text == -1:
				self.win.move(0,0)
				self.win.refresh()
				text = None
		return self.gather()

class Readline(GuiObject):
	"""
prompt for user input, with bindings to that of the default readline implementation
prompt: prompt displayed before the users text
history: a list of strings which constitutes the previously entered set of strings given to the caller of this function during previous calls
text: the default text, entered as if the user had typed it directly
echo: acts as a mask for passwords (set to ' ' in order to not echo any visible character for passwords)
length: the maximum length for this text entry
delimiter: the delimiter between prompt and text
readonly: whether to accept new text
"""
	def __init__(self, screen=None, base=None, y=0, x=0, history=[], prompt=u"input", default=u"", echo=False, maxLength=0, delimiter=u": ", readonly=0, action=""):
		self.value = default
		self.done = 0
		self.base = base
		self.screen = screen
		self.y, self.x = y, x
		self.history = history
		self.historyPos = len(self.history) if self.history else 0
		self.prompt = prompt
		self.delimiter = delimiter
		self.echo = echo
		self.readonly = readonly
		self.maxLength = maxLength
#prompt and delimiter
		self.s = u"%s%s" % (self.prompt,self.delimiter,) if self.prompt else ""
#position in the currently-being-editted text
		self.ptr = 0
#start of text entry "on-screen", should be greater than self.ptr unless there is absolutely no prompt, (in other words, a completely blank line)
#if there's a prompt, startX should be right after the prompt and the delimiter
#if not, startX is going to be wherever self.x is, as that's where our text is going to appear
		self.startX = len(self.s) if self.s else self.x
#put ptr at the end of the current bit of text
		self.currentLine = self.value
		self.ptr = len(self.currentLine)
		self.insertMode = True
		self.lastDraw = None
		self.draw()
		self.action = action

	def externalEdit(self): return None
 
	def getunicode(self, c):
		return chr(c)

	def draw(self):
		d = self.ptr, self.currentLine
		if self.lastDraw and d == self.lastDraw:
			return
		loc = self.x
		t = self.s
		self.screen.move(self.y, self.x)
		self.screen.clrtoeol()
		if self.s:
			self.screen.addstr(self.y, self.x, self.s)
		t = self.currentLine
		cnt = 0
		if self.echo:
			t = str(self.echo)[:1]*len(t)
		self.screen.addstr(self.y, self.startX, "".join(t))
		self.screen.move(self.y, self.startX+self.ptr)
		self.screen.refresh()
		self.lastDraw = self.ptr, self.currentLine

	def handleKey(self, c):
			if c == -1:
				return None
			if c  ==  3:		# ^C
				self.setStatus("Input aborted!")
				self.currentLine = u''
			elif c  ==  10:		# ^J newline
				if self.history != None and self.currentLine:
					self.history.append(self.currentLine)
				self.done = 1
			elif c in (1, 262):		# ^A, Home key
				self.ptr = 0
			elif c in (5, 360):		# ^E, End key
				self.ptr = len(self.currentLine)
			elif c in (2, 260):		# ^B, left arrow
				if self.ptr>0:
					self.ptr -= 1
				else:
					self.beepIfNeeded()
				return 1
			elif c in (6, 261):		# ^f, right arrow
				if self.ptr<len(self.currentLine):
					self.ptr += 1
				else:
					self.beepIfNeeded()
					self.ptr = len(self.currentLine)
				return 1
			elif c  ==  259:		# Up arrow
				if not self.history or self.historyPos == 0: #history will return non-zero if it has content
					self.beepIfNeeded()
					msg = "No history to move up through." if not self.history else "No previous history to move up through."
					self.setStatus(msg)
				elif self.history and self.historyPos>0:
					self.tempLine = self.currentLine
					self.historyPos -= 1
					self.currentLine = self.history[self.historyPos]
					self.ptr = len(self.currentLine)
				else:
					self.setStatus("Something odd occured, readLine, up arrow")
			elif c  ==  258:		# Down arrow
#if there is no history, or we're off the end of the history list (therefore using tempLine), show an error
				if not self.history or self.historyPos>= len(self.history):
					self.beepIfNeeded()
					msg = "No history to move down through." if not self.history else "No more history to move down through."
					self.setStatus(msg)
#otherwise, we've got more history, or tempLine left to view
				elif self.history:
#go ahead and move down
					self.historyPos += 1
#if we're now off the end of the history, pull up tempLine
#maybe user thought they'd typed something and they hadn't, so they can get back to their pre-history command
					if self.historyPos == len(self.history):
						self.currentLine = self.tempLine
#normal history item
					else:
						self.currentLine = self.history[self.historyPos]
#move to the end of this line, history or tempLine
					self.ptr = len(self.currentLine)
				else:
					self.setStatus("Something odd occured, readLine, down arrow")
			elif c in (8, curses.KEY_BACKSPACE, 263):		# ^H, backSpace
				if self.ptr>0:
					self.currentLine = u"%s%s" % (self.currentLine[:self.ptr-1],self.currentLine[self.ptr:])
					self.ptr -= 1
				else:
					self.beepIfNeeded()
			elif c in (4, 330):		# ^D, delete
				if self.ptr<len(self.currentLine):
					self.currentLine = u"%s%s" % (self.currentLine[:self.ptr],self.currentLine[self.ptr+1:])
				else:
					self.beepIfNeeded()
			elif c  ==  331:		# insert
				self.insertMode = False if self.insertMode == True else False
				self.setStatus("insert mode "+"on" if self.insertMode else "off")
			elif c  ==  21:		# ^U
				self.ptr = 0
				self.currentLine = u''
			elif c  ==  11:		# ^K
				self.currentLine = self.currentLine[:self.ptr]
			else:
				if self.readonly:
					self.beepIfNeeded()
					self.setStatus("This is a read only line. Text can not be modified.")
				else:
					uchar = self.getunicode(c)
					if not self.insertMode:
						self.currentLine[self.ptr] = uchar
					else:
						self.currentLine = "%s%s%s" % (self.currentLine[:self.ptr],uchar,self.currentLine[self.ptr:])
						self.ptr += 1
						if self.maxLength>0 and self.ptr >=  self.maxLength:
							if self.history != None and self.currentLine:
								self.history.append(self.currentLine)
							self.done = True
							self.setStatus("Maximum field length reached.")
						#handled keystroke
			self.draw()
			return 1

class Listbox(GuiObject):
	"""Listbox
render a listbox to the screen in `title \n separator \n items` format
y,x: y and x coordinates where to draw this window on the screen
height: maximum height of this window on the screen, including title and separator (defaults to the length of the list, or the height of the window)
base: base clifox object for accessing settings and other clifox state
default: the index of the currently selected item (or a list of selected items, if multiple is true)
title: the title of this select box (might be taken from the element on the webpage)
keysWaitTime: maximum amount of time the system will consider a consecutive set of key-presses as a single search
items: a list of options in string form, or a list of (id,option) tuples
multiple: whether to allow selecting multiple options
"""
	def __init__(self, screen=None, base=None, y=0, x=0, height=None, title=None, items=[], keysWaitTime=0.4, default=0, multiple=False):
		self.screen = screen
		self.base = base
		self.multiple = multiple
		self.y, self.x = y, x
		self.title = title
#if we've got a list of strings or a list of non-list objects, turn them into itemIndex,item
#so ["a","b","c"] would become [[0,"a"],[1,"b"],[2,"c"]]
		if items and type(items[0]) not in (tuple, list):
			items = zip(range(len(items)),items)
		else:
			items = items
		items = [(i,str(j)) for i, j in items]
		self.items = items
		self.keys = []
		self.lastKeyTime = -1
		self.keysWaitTime = keysWaitTime
		if height == None:
			height = (len(self.items)+2) if (len(self.items)+2)<self.base.maxy-2 else self.base.maxy-2
		self.height = height
		if type(default) not in (list, tuple):
			default = [default]
		self.selections = default
		self.pos = self.selections[0]
		self.lastDraw = None
		self.draw()

	def draw(self):
		title = self.title
		windowY = self.y
		listHeight = self.height-2
		start = self.pos//listHeight
		startL = (start*listHeight)
#if startL%lsitHiehgt =  = 0 then we can clear the screen
		endL = (start*listHeight)+listHeight
		sw = windowY+2
		if self.lastDraw != (startL, endL,[i for i in self.selections]):
			show = self.items[startL:endL]
			self.screen.move(windowY, 0)
			self.screen.clrtoeol()
			self.screen.addstr(windowY, 0, title)
			for idx, itm in enumerate(show):
				self.screen.move(idx+sw, 0)
				self.screen.clrtoeol()
				if self.multiple:
					s = "[%s] %s" % (("+" if startL+idx in self.selections else "-"),itm[1],)
				else:
					s = "%s" % (itm[1],)
				self.screen.addstr(idx+sw, 0, s)
		self.lastDraw = (startL, endL,[i for i in self.selections])
		self.screen.move(sw+(self.pos-startL), 0)
#		self.setStatus("height = %d:startL = %d:endL = %d:pos = %d" % (self.height,startL,endL,sw+self.pos-startL))
		self.screen.refresh()

	def search(self, key):
		t = time.time()
		if key in string.printable and (self.keys and t-self.lastKeyTime<self.keysWaitTime):
			self.keys.append(key)
			self.lastKeyTime = t
		else:
			self.keys = [key]
		keys = "".join(self.keys)
		keys = keys.lower()
		j = -1
		for i in self.items:
			j += 1
			if str(i[1]).lower().startswith(keys):
				self.pos = j
				break

	def handleKey(self, c):
		if c == -1:
			return None
		if self.multiple and c == 32:
			if self.pos in self.selections:
				self.selections.remove(self.pos)
			else:
				self.selections.append(self.pos)
		elif curses.ascii.isprint(c):
			self.search(chr(c))
		elif c == curses.KEY_UP:
			if self.pos == 0:
#we don't want to wrap around to the top
				pass #self.pos = len(self.items)-1
				self.beepIfNeeded()
			else:
				self.pos -= 1
		elif c == curses.KEY_DOWN:
			if self.pos == len(self.items)-1:
				pass #self.pos = 0
				self.beepIfNeeded()
			else:
				self.pos += 1
		elif c in (10, 261): # newline or right arrow
			self.done = 1
			return self.selections if self.multiple else self.pos
		elif c == 260: # left arrow quietly back out
			self.done = 1
			return self.selections if self.multiple else self.pos
		self.draw()


class question(Listbox):

	def handleKey(self, c):
		if c == -1:
			return None
		if c == curses.KEY_UP:
			if self.pos == 0:
#we don't want to wrap around to the top
				self.base.setStatus(self.title)
				pass #self.pos = len(self.items)-1
#				return 1
			else:
				self.pos -= 1
		elif c == curses.KEY_DOWN:
			if self.pos == len(self.items)-1:
				self.setStatus(self.title) #self.pos = 0
#				return 1
			else:
				self.pos += 1
		elif c in (10, 261): # newline or right arrow
			self.done = 1
			return self.selections if self.multiple else self.pos
		elif c == 260: # left arrow quietly back out
			self.done = -1
			return self.selections if self.multiple else self.pos
		self.draw()

class fileBrowser(Listbox):

	def __init__(self, dir="./", select_type="file", action="", prev_items=[], extensions=None, hidden_files=False, *args, **kwargs):
		self.select_type = select_type
		self.selected_action = action
		self.dir = dir
		self.prev_items = prev_items
		self.extensions = extensions
		self.hidden_files = hidden_files
		items = self.make_list()
		super(fileBrowser, self).__init__(items=items, *args, **kwargs)

	def make_list(self):
		self.pos = 0
		files = []
		folders = []
		os.chdir(self.dir)
		self.back_directory = os.path.abspath("..")
		for i in self.prev_items:
			folders.append((i, i))
		for i in sorted(os.listdir(self.dir)):
			if i.startswith(".") and self.hidden_files == False:
				continue
			if os.path.isdir(i):
				folders.append((os.path.abspath(i), i))
			else:
				if self.extensions != None:
					ext = i.split(".")[-1]
					if ext not in self.extensions:
						continue
				files.append((os.path.abspath(i), i))
		folders.extend(files)
		return folders

	def getDir(self):
		return self.items[self.pos][0]

	def expand(self):
		self.dir = self.getDir()
		self.items = self.make_list()
		self.lastDraw = None
		self.draw()

	def collapse(self):
		self.dir = self.back_directory
		self.items = self.make_list()
		self.lastDraw = None
		self.draw()

	def handleKey(self, c):
		if c == -1:
			return None
		if self.multiple and c == 32:
			if self.pos in self.selections:
				self.selections.remove(self.pos)
			else:
				self.selections.append(self.pos)
			return 1
		elif curses.ascii.isprint(c):
			self.search(chr(c))
#			return 1
		elif c == curses.KEY_UP:
			if self.pos == 0:
#we don't want to wrap around to the top
				pass #self.pos = len(self.items)-1
				self.beepIfNeeded()
			else:
				self.pos -= 1
		elif c == curses.KEY_DOWN:
			if self.pos == len(self.items)-1:
				pass #self.pos = 0
				self.beepIfNeeded()
			else:
				self.pos += 1
		elif c in (10, 261, curses.KEY_RIGHT): # newline or right arrow
			if self.getDir() in self.prev_items and self.selected_action != "":
				self.done = 1
				self.dir = self.getDir()
				return 1
			elif os.path.isfile(self.getDir()) and self.select_type == "file" and self.selected_action != "":
				self.done = 1
				self.dir = self.getDir()
				self.setStatus(self.dir)
				return 1
			if os.path.isdir(self.getDir()) and self.select_type != "file":
				self.done = 1
				return 1
			if os.path.isdir(self.getDir()):
				self.expand()
				return 1
		elif c == curses.KEY_LEFT or c == curses.KEY_BACKSPACE: # left arrow quietly back out
			self.collapse()
			return 1
		self.draw()

