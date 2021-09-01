# Python program raising
# exceptions in a python
# thread
import logging
import threading
import ctypes
import time

# from nlu.data_process.train import status_map
from nlu.status import nlu_status_map

logger = logging.getLogger(__name__)


class ThreadWithException(threading.Thread):
    def __init__(self, target, kwargs=None, name=None):
        threading.Thread.__init__(self, target=target, name=name, kwargs=kwargs)
        self.name = name

    def get_id(self):

        # returns id of the respective thread
        if hasattr(self, 'ident'):
            return self.ident
        for id, thread in threading._active.items():
            if thread is self:
                return id

    def raise_exception(self):
        logger.debug("Into raise_exception")
        thread_id = self.get_id()

        # 设置线程的状态为SystemExit，主线程不影响
        # 返回res是否设置成功
        # 只有返回1才表示设置成功
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread_id),
                                                         ctypes.py_object(SystemExit))
        logger.debug("res=%d" % res)
        if res == 0:
            raise ValueError("invalid thread id")
        elif res > 1:
            # if it returns a number greater than one, you're in trouble,
            # and you should call it again with exc=NULL to revert the effect
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)  # TODO 是None还是0
            raise SystemError("PyThreadState_SetAsyncExc failed")



if __name__ == '__main__':
    def sing():
        for i in range(3):
            print("正在唱歌...%d" % i)
            time.sleep(1)


    def dance():
        for i in range(3):
            print("正在跳舞...%d" % i)
            time.sleep(1)
    t1 = ThreadWithException(name='Thread 1', target=sing)
    t2 = ThreadWithException(name='Thread 2', target=dance)
    t1.start()
    t2.start()
    # time.sleep(2)
    # t1.raise_exception()
    # t2.raise_exception()
    t1.join()
