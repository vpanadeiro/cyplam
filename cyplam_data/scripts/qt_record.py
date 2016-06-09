#!/usr/bin/env python
import os
import sys
import time
import rospy
import rospkg

from python_qt_binding import loadUi
from python_qt_binding import QtGui
from python_qt_binding import QtCore

from mashes_measures.msg import MsgStatus
from move_data.move_data import move_file


TOPICS = ['/tachyon/image',
          '/tachyon/geometry',
          '/control/power',
          '/joint_states']


class QtRecord(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        path = rospkg.RosPack().get_path('cyplam_data')
        loadUi(os.path.join(path, 'resources', 'record.ui'), self)

        self.btnRecord.clicked.connect(self.btnClickRecord)

        home = os.path.expanduser('~')
        self.dirdata = os.path.join(home, 'bag_data')
        if not os.path.exists(self.dirdata):
            os.mkdir(self.dirdata)
        self.filename = ''

        rospy.Subscriber(
            '/supervisor/status', MsgStatus, self.cbStatus, queue_size=1)
        self.status = False
        self.running = False

        self.process = QtCore.QProcess(self)
        #self.process.readyRead.connect(self.dataReady)

    def btnClickRecord(self):
        self.running = not self.running
        if self.running:
            self.btnRecord.setText('Ready for Data')
            self.txtOutput.textCursor().insertText('> ready for data.\n')
        else:
            self.btnRecord.setText('Record Data')
            self.txtOutput.textCursor().insertText('> stopped.\n')

    def cbStatus(self, msg_status):
        if not self.status and msg_status.running:
            if self.running:
                self.btnRecord.setText('Recording...')
                self.txtOutput.textCursor().insertText('> recording topics:\n%s\n' % '\n'.join(TOPICS))
                self.callProgram()
        elif self.status and not msg_status.running:
            self.running = False
            self.killProgram()
            self.btnRecord.setText('Record Data')
            self.txtOutput.textCursor().insertText('> %s recorded.\n' % self.filename)
        self.status = msg_status.running

    def dataReady(self):
        cursor = self.txtOutput.textCursor()
        cursor.movePosition(cursor.End)
        text = str(self.process.readAll())
        cursor.insertText(text)
        self.txtOutput.ensureCursorVisible()

    def callProgram(self):
        os.chdir(self.dirdata)
        self.filename = 'data_' + time.strftime('%Y%m%d-%H%M%S') + '.bag'
        self.process.start(
            'rosrun rosbag record -O %s %s' % (self.filename, ' '.join(TOPICS)))

    def killProgram(self):
        os.system('killall -2 record')
        self.process.waitForFinished()
        move_file(os.path.join(self.dirdata, self.filename), '/home/ryco/data/')
        self.txtOutput.textCursor().insertText('> %s transfered.\n' % self.filename)


if __name__ == '__main__':
    rospy.init_node('record_panel')

    app = QtGui.QApplication(sys.argv)
    qt_record = QtRecord()
    qt_record.show()
    app.exec_()
