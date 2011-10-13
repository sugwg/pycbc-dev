// Copyright (C) 2011 Karsten Wiesner
//
// This program is free software; you can redistribute it and/or modify it
// under the terms of the GNU General Public License as published by the
// Free Software Foundation; either version 2 of the License, or (at your
// option) any later version.
//
// This program is distributed in the hope that it will be useful, but
// WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
// Public License for more details.
//
// You should have received a copy of the GNU General Public License along
// with this program; if not, write to the Free Software Foundation, Inc.,
// 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.


//
// =============================================================================
//
//                                   Preamble
//
// =============================================================================
//
// pycbcopencl declarations that are not going to be swig wrapped 
// thus they are private property of the clayer


#ifndef PYCBCOPENCL_PRIVATE_H
#define PYCBCOPENCL_PRIVATE_H

#include <stdlib.h>

#define ERROR_STRING_LEN 512 

extern unsigned pycbcopencl_error_stash;
extern char pycbcopencl_error_message[ERROR_STRING_LEN];

// pycbc opencl error functions
int pycbc_opencl_check_error(void);
char* pycbc_opencl_get_error_message(void);
void pycbc_opencl_set_error(int, char*);
void pycbc_opencl_clear_error(void);

// prototypes of all methodes that will extend pure c typedefs
cl_context_t* new_cl_context_t(unsigned);
void delete_cl_context_t( cl_context_t* );


#endif /* PYCBCOPENCL_PRIVATE_H */