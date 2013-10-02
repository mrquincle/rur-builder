from omniidl import idltype
from helper import visit

def enum(*sequential, **named):
	enums = dict(zip(sequential, range(len(sequential))), **named)
	return type('Enum', (), enums)

Direction = enum('IN','OUT','INOUT')

class RurModule(visit.Visit) :

	def writeFileComment(self):
		comment_text = '''/**
 * This file is created at Almende B.V. It is open-source software and part of the Common 
 * Hybrid Agent Platform (CHAP). A toolbox with a lot of open-source tools, ranging from 
 * thread pools and TCP/IP components to control architectures and learning algorithms. 
 * This software is published under the GNU Lesser General Public license (LGPL).
 *
 * It is not possible to add usage restrictions to an open-source license. Nevertheless,
 * we personally strongly object against this software being used by the military, in the
 * bio-industry, for animal experimentation, or anything that violates the Universal
 * Declaration of Human Rights.
 *'''
		print comment_text
		for p in self.pragmaList:
			print " * @" + p.text()
		print " */"
		print

	# Return different convenient configuration fields for a port. There should be only one parameter
	# per port, more will probably result in errors and are not part of the rur-builder IDL definition
	# Returns:
	# 	port			used to define the port object, e.g. portOutput
	# 	port_name		the name specific part, used for multiple purposes, e.g. Output
	#	port_direction		in/out
	#	port_param_name		the name of the variable is used for the port name, e.g. /output
	#	port_param_type		the type of the variable, e.g. int
	#	port_param_kind		the kind of the variable, as defined in idltype.py
	def getPortConfiguration(self, portobject):
		params = portobject.parameters()
		if len(params) != 1:
			self.st.out("//! Warning: wrong number of parameters used in the .idl file")
		port_name = portobject.identifier()
		port = "port" + port_name
		port_param = params[0]
		port_param_name = port_param.identifier()
		port_param_type = self.getParamType(port_param)
		port_param_kind = self.getParamKind(port_param)
		pragmas = portobject.pragmas()
		comments = portobject.comments()
		
		port_pragmas = []
		for pr in pragmas:
			port_pragmas.append(pr.text())
		
		port_comments = []
		for co in comments:
			port_comments.append(co.text())
		
		if port_param.is_in():
			port_direction = Direction.IN
		elif port_param.is_out():
			port_direction = Direction.OUT
		elif port_param.direction() == 2:
			self.st.out("//! Warning: inout is not supported")
			port_direction = Direction.INOUT
		else:
			self.st.out("//! Warning: no proper direction for port defined in .idl file")
		return port, port_name, port_direction, port_param_name, port_param_type, port_param_kind, port_pragmas, port_comments

	# The function for each port is defined by a preceding "read" or "write", e.g. writeOutput
	def getPortFunctionName(self, port_name):
		if port_direction == Direction.IN:
			function_name = "read" + port_name
		if port_direction == Direction.OUT:
			function_name = "write" + port_name
		return function_name

## Write Functions

	def writePortFunctionSignature(self, portobject):
		port, port_name, port_direction, param_name, param_type, param_kind, port_pragmas, port_comments = self.getPortConfiguration(portobject)
		if port_direction == Direction.IN:
			self.st.out("// Read from this function and assume it means something")
			if param_kind == idltype.tk_sequence:
				self.st.out("// Remark: caller is responsible for evoking vector->clear()")
			else:
				self.st.out("// Remark: check if result is not NULL")
			self.st.out(param_type + " *read" + port_name + "(bool blocking=false);")
			self.st.out("")
		if port_direction == Direction.OUT:
			self.st.out("// Write to this function and assume it ends up at some receiving module")
			if param_kind == idltype.tk_sequence:
				self.st.out("bool write" + port_name + "(const " + param_type + " &" + param_name + ");")
			else:
				self.st.out("bool write" + port_name + "(const " + param_type + " " + param_name + ");")
			self.st.out("")

	def writePortFunctionSignatureImpl(self, portobject, direction):
		port, port_name, port_direction, param_name, param_type, param_kind, port_pragmas, port_comments = self.getPortConfiguration(portobject)
		if direction == Direction.IN:
			self.st.out(param_type + "* " + self.classname + "::read" + port_name + "(bool blocking) {")
		if direction == Direction.OUT:
			if param_kind == idltype.tk_sequence:
				self.st.out("bool " + self.classname + "::write" + port_name + "(const " + param_type + " &" + param_name + ") {")
			else:
				self.st.out("bool " + self.classname + "::write" + port_name + "(const " + param_type + " " + param_name + ") {")
		self.st.inc_indent()

	def writeFunctionEnd(self):
		self.st.dec_indent()
		self.st.out("}")

	def writeIncludeGuardStart(self):
		print "#ifndef " + self.classname.upper() + "_H_"
		print "#define " + self.classname.upper() + "_H_"
		print ""

	def writeIncludeGuardEnd(self):
		print "#endif // " + self.classname.upper() + "_H_"

	def writeClassStart(self):
		self.st.out("class " + self.classname + " {")

	def writeClassEnd(self):
		self.st.dec_indent()
		self.st.out("};")
