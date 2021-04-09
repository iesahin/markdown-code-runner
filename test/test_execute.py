
import unittest
import mdcoderun
from mdcoderun import execute

class ExecuteTestCase(unittest.TestCase):
    def test_get_client(self):
        c = execute.get_client()
        self.assertIsNotNone(c, f"Client is None")

    def test_get_container(self):
        c = execute.get_container("bash")
        self.assertIsNotNone(c, "Container is None")

    def test_run_in_container(self):
        exit_codes, res = execute.run_in_container("bash", "echo 'hello world'")
        self.assertEqual(exit_codes, [0])
        self.assertEqual(res, "hello world\n")

        exit_codes, res = execute.run_in_container("bash", "$ echo 'hello dollar'")
        self.assertEqual(exit_codes, [0])
        self.assertEqual(res, "hello dollar\n")

        exit_codes, res = execute.run_in_container("bash", """$ echo \\
                                                            'hello split'""")
        self.assertEqual(exit_codes, [0])
        self.assertEqual(res, "hello split\n")

        exit_codes, res = execute.run_in_container("bash", """echo 'hello world'
echo 'hi mars'
        """)
        self.assertEqual(exit_codes, [0, 0])
        self.assertEqual(res, """hello world

hi mars
""")

    def test_run_in_child_container(self):
        output = execute.run_in_child_container("bash", "echo 'hello world'")
        self.assertEqual(output, "hello world\n")

        output = execute.run_in_child_container("bash", """
$ echo 'hello dollar'

$ pwd 

$ echo \
    'hello \
        split'
        """ )
        self.assertEqual(output, 
"""hello dollar
/
hello         split
""")


def suite():
    suite = unittest.TestSuite()
    suite.addTest(ExecuteTestCase('test_get_client'))
    suite.addTest(ExecuteTestCase('test_get_container'))
    suite.addTest(ExecuteTestCase('test_run_in_container'))
    suite.addTest(ExecuteTestCase('test_run_in_child_container'))

    return suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
