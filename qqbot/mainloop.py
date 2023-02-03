# -*- coding: utf-8 -*-

import sys, os
p = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if p not in sys.path:
    sys.path.insert(0, p)

import traceback

from common import StartDaemonThread
import queue

def workAt(taskQueue):
    while True:
        try:
            func, args, kwargs = taskQueue.get(timeout=0.5)
        except queue.Empty:pass
        except:traceback.print_exc()
        else:
            # func(*args, **kwargs)
            try:
                func(*args,**kwargs)
            except SystemExit:raise
            except:traceback.print_exc()

class TaskLoop(object):
    def __init__(self):
        self.mainQueue = queue.Queue()
        self.childQueues = {}    

    # Put a task into `mainQueue`, it will be executed in the main thread.
    # So all tasks you `Put` will be executed one after another. Means that
    # you can access the global data safely in these tasks.
    # 将任务放入(Put)`mainQueue`，它将在主线程中执行。
    # 因此，您`放置`(Put)的所有任务都将一个接一个地执行。意味着
    # 您可以在这些任务中安全地访问全局数据。
    def Put(self, func, *args, **kwargs):
        self.mainQueue.put((func, args, kwargs))

    # Put a task into a child queue which with label `queueLabel`. It will be
    # executed in a child thread. Normally, it is a good idea to put an IO
    # task into a child queue, and when this task finishs his job, he put
    # a committing task with his result into the main queue.
    # At first, there is only one worker(thread) works on a child queue. You
    # can call `AddWorkerTo` to add workers(threads) to a child queue.
    # 将任务放入标签为`queueLabel`的子队列。会的
    # 在子线程中执行。通常，放置IO是一个好主意
    # 任务放入子队列，当该任务完成其工作时，他将
    # 将其结果提交到主队列的任务。
    # 首先，一个子队列上只有一个工作线程。你
    # 可以调用'AddWorkerTo'将工作线程添加到子队列。
    def PutTo(self, queueLabel, func, *args, **kwargs):
        self.Put(self.putTo, queueLabel, func, args, kwargs)

    def putTo(self, queueLabel, func, args, kwargs):
        if queueLabel in self.childQueues:
            self.childQueues[queueLabel].put((func, args, kwargs))
        else:
            self.childQueues[queueLabel] = queue.Queue()
            self.childQueues[queueLabel].put((func, args, kwargs))
            StartDaemonThread(workAt, self.childQueues[queueLabel])

    def AddWorkerTo(self, queueLabel, n):
        self.Put(self.addWorkerTo, queueLabel, n)

    def addWorkerTo(self, queueLabel, n):
        if queueLabel not in self.childQueues:
            self.childQueues[queueLabel] = queue.Queue()
        for i in range(n):
            StartDaemonThread(workAt, self.childQueues[queueLabel])

    def Run(self):
        workAt(self.mainQueue)

mainLoop = TaskLoop()
MainLoop = mainLoop.Run
Put = mainLoop.Put
PutTo = mainLoop.PutTo
AddWorkerTo = mainLoop.AddWorkerTo