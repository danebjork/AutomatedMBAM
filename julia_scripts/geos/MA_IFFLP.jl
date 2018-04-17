module T
import Models
import Geometry
include("/Users/dane/auto_mbam/julia_scripts/models/MA_IFFLP.jl")
include("/Users/dane/auto_mbam/geosender.jl")
model = MA_IFFLP_Model.model
xi = MA_IFFLP_Model.xi
v = Geometry.Geodesics.vi(xi, model.jacobian, model.Avv)
integrator = Models.GeodesicIntegrator(model, xi, v, tmax=1.0, lambda=0.0, abstol=0.001, reltol=0.001, use_svd=false, use_pinv=false)
start = Dict("x"=> [], "v"=> [], "tau"=> [], "t"=> [], "j"=>[])
try
	while true
		Geometry.Geodesics.step!(integrator)
		sol = Geometry.Geodesics.solution(integrator)
		j = model.jacobian(sol.xs[end, :])
		update = Dict(
			"x"=>sol.xs[end, :],
			"v"=>sol.vs[end, :],
			"tau"=>sol.τs[end, :],
			"t"=>sol.ts[end, :],
			"j"=>j,
		)
		push = false
		while !push
			try
				GeoSender.send_to_py(update)
				push = true
			catch
				sleep(.4)
			end
		end
	end
catch E
	println(E)
	GeoSender.send_to_py(Dict("done"=> "except"))
end
end # module