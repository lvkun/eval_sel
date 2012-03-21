#!/usr/bin/python

import sublime, sublime_plugin
import os, subprocess, threading, functools

SETTINGS_FILE = "eval_sel.sublime-settings"

class readThread(threading.Thread):  
    def __init__(self, process, file_io, output):  
        self.file_io = file_io
        self.output = output
        self.process = process
        threading.Thread.__init__(self)
    
    def run(self):
        if not self.file_io:
            return

        while True:
            line = self.file_io.readline()
            
            if len(line) == 0:
                break;

            sublime.set_timeout(functools.partial(self.output, 
                        "%s" % (line)), 0)

class evalselCommand(sublime_plugin.TextCommand):
    
    def __init__(self, view):
        self.view = view
        self.output_view = None

        self.process = None
        self.out_thread = None

    def __del__(self):
        self.close_process()

    def getLang(self):
        scopes = self.view.settings().get('syntax')
        lang = scopes.split("/")[1]
        return lang

    def open_process(self):
        if self.process and (not self.process.poll()):
            return True

        lang = self.getLang()
        evaluator = sublime.load_settings(SETTINGS_FILE).get(lang, "").split()
        print evaluator
        if len(evaluator) == 0:
            return False

        self.process = subprocess.Popen(evaluator, 
            stdin=subprocess.PIPE, 
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        
        # re-start new thread when open new subprocess
        self.run_read_thread()

        return True

    def close_process(self):
        if self.process:
            self.process.kill()

    def run_read_thread(self):
        self.out_thread = readThread(self.process, 
            self.process.stdout, 
            self.output)
        self.out_thread.start()

    def run(self, edit):
        # always show output panel
        self.show_output_view()

        if self.open_process():
            sel = self.view.sel()[0]
            expression = self.view.substr(sel)
            
            self.eval(expression)
    
    def scroll_to_view_end(self):
        (cur_row, _) = self.output_view.rowcol(self.output_view.size())
        self.output_view.show(self.output_view.text_point(cur_row, 0))

    def output(self, info):
        self.output_view.set_read_only(False)
        edit = self.output_view.begin_edit()
        
        self.output_view.insert(edit, self.output_view.size(), info)
        self.scroll_to_view_end()

        self.output_view.end_edit(edit)
        self.output_view.set_read_only(True)

    def show_output_view(self):
        if not self.output_view:
            self.output_view = self.view.window().get_output_panel("evalsel")
        self.view.window().run_command('show_panel', {'panel': 'output.evalsel'})

    def eval(self, expression):
        self.process.stdin.write(expression + "\n")
        self.process.stdin.flush()