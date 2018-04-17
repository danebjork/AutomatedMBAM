
module MA_IFFLP_P11H0_Model

import Models
import ParametricModels
using Parameters

@with_kw type MA_IFFLP_P11H0{T<:Real} <: ParametricModels.AbstractParameterSpace{T} @deftype T
	A_init = 0.0
	A_total = 1.0
	B_init = 0.0
	B_total = 1.0
	C_init = 0.0
	C_total = 1.0
	K_1 = 0.00034740515734076646
	K_3 = 0.0014987921041355774
	K_4 = 47.75910894614586
	K_5 = 0.003405248745625123
	K_6 = 0.38922566298290584
	k_1 = 0.23249411781670218
	k_2 = 0.03602541983581194
	k_3 = 0.20475153357375242
	k_4 = 0.045114133207701496
	k_5 = 0.5236551721745745
	k_6 = 1.3347187880650755
end

function inp{T<:Real}(ps::MA_IFFLP_P11H0{T}, _t)
	return T[]
end

function ic{T<:Real}(ps::MA_IFFLP_P11H0{T})
	return T[ps.A_init, ps.B_init, ps.C_init]
end

function rhs{T<:Real}(ps::MA_IFFLP_P11H0{T}, _t, _x, _dx)
	A_inact = -_x[1] + ps.A_total
	B_inact = -_x[2] + ps.B_total
	C_inact = -_x[3] + ps.C_total
	_inp = inp(ps, _t)
	_dx[1] = A_inact.*ps.k_1./(A_inact + ps.K_1) - A_inact.*ps.k_2./(A_inact + ps.K_1) - ps.K_1.*ps.k_2./(A_inact + ps.K_1)
	_dx[2] = B_inact.*_x[1].*_x[2].*ps.k_3./(B_inact.*_x[2] + B_inact.*ps.K_4 + _x[2].*ps.K_3 + ps.K_3.*ps.K_4) + B_inact.*_x[1].*ps.K_4.*ps.k_3./(B_inact.*_x[2] + B_inact.*ps.K_4 + _x[2].*ps.K_3 + ps.K_3.*ps.K_4) - B_inact.*_x[2].*ps.k_4./(B_inact.*_x[2] + B_inact.*ps.K_4 + _x[2].*ps.K_3 + ps.K_3.*ps.K_4) - _x[2].*ps.K_3.*ps.k_4./(B_inact.*_x[2] + B_inact.*ps.K_4 + _x[2].*ps.K_3 + ps.K_3.*ps.K_4)
	_dx[3] = C_inact.*_x[1].*_x[3].*ps.k_5./(C_inact.*_x[3] + C_inact.*ps.K_6 + _x[3].*ps.K_5 + ps.K_5.*ps.K_6) + C_inact.*_x[1].*ps.K_6.*ps.k_5./(C_inact.*_x[3] + C_inact.*ps.K_6 + _x[3].*ps.K_5 + ps.K_5.*ps.K_6) - C_inact.*_x[2].*_x[3].*ps.k_6./(C_inact.*_x[3] + C_inact.*ps.K_6 + _x[3].*ps.K_5 + ps.K_5.*ps.K_6) - _x[2].*_x[3].*ps.K_5.*ps.k_6./(C_inact.*_x[3] + C_inact.*ps.K_6 + _x[3].*ps.K_5 + ps.K_5.*ps.K_6)
	nothing
end

function obs{T<:Real}(ps::MA_IFFLP_P11H0{T}, _t, _x)
	return T[_x[3]]
end

import HDF5
ydata = HDF5.h5read("/Users/dane/auto_mbam/temp.h5", "/ydata")
_t = HDF5.h5read("/Users/dane/auto_mbam/temp.h5", "/t")
data = ParametricModels.OLSData("MA_IFFLP_P11H0", ydata)
parametricmodel = @ParametricModels.ODEModel(data, MA_IFFLP_P11H0, ic, rhs, obs, _t, (), Tuple{Symbol, Any}[])
@ParametricModels.SetConstant(parametricmodel, A_init, A_total, B_init, B_total, C_init, C_total)
for p in parametricmodel.parameters
	if p.s in [:K_1, :K_3, :K_4, :K_5, :K_6, :k_1, :k_2, :k_3, :k_4, :k_5, :k_6]
		p.t = exp
		p.invt = log
	elseif p.s in []
		p.t = sinh
		p.invt = asinh
	end
end

model = Models.Model(parametricmodel)
xi = ParametricModels.xvalues(parametricmodel)
end # module