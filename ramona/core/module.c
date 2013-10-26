#include "ramona_core.h"

/* Available functions */
static PyObject *get_libev_version(PyObject *self);

/* Module specification */
static PyMethodDef module_methods[] = {
    {"get_libev_version", (PyCFunction)get_libev_version, METH_NOARGS, "Get version of libev."},
    {NULL, NULL, 0, NULL}
};

// allocate memory from the Python heap
static void * python_allocator(void *ptr, long size)
{
    if (size) {
        return PyMem_Realloc(ptr, size);
    }
    PyMem_Free(ptr);
    return NULL;
}

/* Initialize the module */
PyObject * init_core(void)
{
    PyObject *module = Py_InitModule3(
    	"core",
    	module_methods,
    	"Internal Ramona C module that provides optimalized interface to LibEv."
    );
    if (module == NULL) return NULL; // Initialization failed




	// Connect libev with Python environment
    ev_set_allocator(python_allocator);
    ev_set_syserr_cb(Py_FatalError);

    // Return module
    return module;

fail:
#if PY_MAJOR_VERSION >= 3
    Py_DECREF(pyev);
#endif
    return NULL;
}

// Initialization function used by Python2.x
PyMODINIT_FUNC initcore(void)
{
    init_core();
}

///////////////////////////////////////////////////////////////////////////////

static PyObject *get_libev_version(PyObject *self)
{
	return Py_BuildValue("ii", ev_version_major(), ev_version_minor());
}
