class ramona_runtime_errorbase(RuntimeError):
	exitcode = 100

class server_not_responding_error(ramona_runtime_errorbase):
	exitcode = 2

class server_start_error(ramona_runtime_errorbase):
	exitcode = 3
