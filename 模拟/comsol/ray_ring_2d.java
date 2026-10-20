import com.comsol.model.*;
import com.comsol.model.util.*;

/**
 * Ring-spectrum project - Ray Optics 2D cross-section verification.
 *
 * A diametral slice through the disc axis. Collimated light travels along the
 * disc axis (normal incidence on the track grating). The Grating feature splits
 * it into diffraction orders; +/-1 orders leave at angle beta with
 * sin(beta)=lambda/d on either side, then propagate to a screen at distance L.
 * The two landing spots sit at x = +/- L*tan(beta). Sweeping wavelength checks
 * that the ring radius rho = L*tan(beta(lambda)) separates as expected.
 *
 * This is a GEOMETRY validation: order reflectances are set to a fixed value
 * (not yet coupled to the wave-optics S-parameters), so only ray directions and
 * screen landing positions are meaningful, not intensities.
 */
public class ray_ring_2d {

  public static void main(String[] args) {
    Model model = run();
    String out = "C:/Users/qiann/Desktop/TJPT光栅/模拟/comsol/ray_ring_2d.mph";
    try { model.save(out); } catch (Exception e) { }
  }

  public static Model run() {
    Model model = ModelUtil.create("Model");
    model.modelPath("C:/Users/qiann/Desktop/TJPT光栅/模拟/comsol");

    // ---- parameters ----
    model.param().set("d", "0.74[um]", "track pitch (DVD)");
    model.param().set("L", "300[mm]", "disc-to-screen distance");
    model.param().set("lam", "550[nm]", "vacuum wavelength");
    model.param().set("f0", "c_const/lam", "optical frequency");
    model.param().set("halfW", "40[mm]", "grating half width on disc (illuminated region)");
    model.param().set("scrW", "200[mm]", "screen half width");
    model.param().set("Rfix", "0.35", "fixed order reflectance (placeholder)");

    model.component().create("comp1", true);
    model.component("comp1").geom().create("geom1", 2);
    model.component("comp1").geom("geom1").lengthUnit("mm");
    model.component("comp1").mesh().create("mesh1");

    // Disc plane (the grating line) at y=0, screen at y=L.
    // Air box: x in [-scrW, scrW], y in [-5, L+5]
    model.component("comp1").geom("geom1").create("r1", "Rectangle");
    model.component("comp1").geom("geom1").feature("r1").set("size", new String[]{"2*scrW", "L+10[mm]"});
    model.component("comp1").geom("geom1").feature("r1").set("pos", new String[]{"-scrW", "-5[mm]"});
    // The grating: a line segment on y=0 from -halfW..halfW (interior boundary)
    model.component("comp1").geom("geom1").create("b1", "BezierPolygon");
    // Use a simple polygon edge for the grating boundary instead:
    model.component("comp1").geom("geom1").feature().remove("b1");
    model.component("comp1").geom("geom1").create("pol1", "Polygon");
    model.component("comp1").geom("geom1").feature("pol1").set("source", "table");
    model.component("comp1").geom("geom1").feature("pol1").setIndex("table", "-halfW", 0, 0);
    model.component("comp1").geom("geom1").feature("pol1").setIndex("table", 0, 0, 1);
    model.component("comp1").geom("geom1").feature("pol1").setIndex("table", "halfW", 1, 0);
    model.component("comp1").geom("geom1").feature("pol1").setIndex("table", 0, 1, 1);
    model.component("comp1").geom("geom1").run("fin");

    // Selections
    // grating boundary (the interior edge on y=0)
    model.component("comp1").selection().create("sel_grat", "Box");
    model.component("comp1").selection("sel_grat").geom("geom1", 1);
    model.component("comp1").selection("sel_grat").set("entitydim", "1");
    model.component("comp1").selection("sel_grat").set("xmin", "-halfW-1");
    model.component("comp1").selection("sel_grat").set("xmax", "halfW+1");
    model.component("comp1").selection("sel_grat").set("ymin", "-0.5");
    model.component("comp1").selection("sel_grat").set("ymax", "0.5");
    // screen boundary (top edge y=L)
    model.component("comp1").selection().create("sel_scr", "Box");
    model.component("comp1").selection("sel_scr").geom("geom1", 1);
    model.component("comp1").selection("sel_scr").set("entitydim", "1");
    model.component("comp1").selection("sel_scr").set("xmin", "-scrW-1");
    model.component("comp1").selection("sel_scr").set("xmax", "scrW+1");
    model.component("comp1").selection("sel_scr").set("ymin", "L-0.5");
    model.component("comp1").selection("sel_scr").set("ymax", "L+0.5");

    // medium: air everywhere
    model.component("comp1").material().create("mat1", "Common");
    model.component("comp1").material("mat1").propertyGroup("def")
         .set("relpermittivity", new String[]{"1"});
    model.component("comp1").material("mat1").propertyGroup("def")
         .set("relpermeability", new String[]{"1"});
    model.component("comp1").material("mat1").propertyGroup("def")
         .set("electricconductivity", new String[]{"0"});
    model.component("comp1").material("mat1").selection().all();

    // ---- Geometrical Optics ----
    model.component("comp1").physics().create("gop", "GeometricalOptics", "geom1");
    model.component("comp1").physics("gop").prop("IntensityComputation")
         .setIndex("IntensityComputation", "ComputeIntensity", 0);
    model.component("comp1").physics("gop").feature("op1")
         .set("RayPropertySpecification", "SpecifyFrequency");
    model.component("comp1").physics("gop").feature("op1").set("nu", "f0");


    // Grating on the disc line
    model.component("comp1").physics("gop").create("grat1", "Grating", 1);
    model.component("comp1").physics("gop").feature("grat1").selection().named("sel_grat");
    model.component("comp1").physics("gop").feature("grat1").set("dg", "d");
    model.component("comp1").physics("gop").feature("grat1").set("StoreTotalTransmittedPower", true);
    model.component("comp1").physics("gop").feature("grat1").set("StoreTotalReflectedPower", true);
    // order 0
    model.component("comp1").physics("gop").feature("grat1").feature("dfo1").set("Rf", "Rfix");
    model.component("comp1").physics("gop").feature("grat1").feature("dfo1").set("Tr", "0");
    // order -1
    model.component("comp1").physics("gop").feature("grat1").create("dfo2", "DiffractionOrder", 1);
    model.component("comp1").physics("gop").feature("grat1").feature("dfo2").set("mg", -1);
    model.component("comp1").physics("gop").feature("grat1").feature("dfo2").set("Rf", "Rfix");
    model.component("comp1").physics("gop").feature("grat1").feature("dfo2").set("Tr", "0");
    // order +1
    model.component("comp1").physics("gop").feature("grat1").create("dfo3", "DiffractionOrder", 1);
    model.component("comp1").physics("gop").feature("grat1").feature("dfo3").set("mg", 1);
    model.component("comp1").physics("gop").feature("grat1").feature("dfo3").set("Rf", "Rfix");
    model.component("comp1").physics("gop").feature("grat1").feature("dfo3").set("Tr", "0");

    // Screen: a wall that records deposition (Freeze = stop rays there)
    model.component("comp1").physics("gop").create("wall1", "Wall", 1);
    model.component("comp1").physics("gop").feature("wall1").selection().named("sel_scr");
    model.component("comp1").physics("gop").feature("wall1").set("WallCondition", "Freeze");

    // Release: collimated rays from just below the grating, going +y (normal).
    model.component("comp1").physics("gop").create("relg1", "ReleaseGrid", -1);
    model.component("comp1").physics("gop").feature("relg1").setIndex("x0", "-halfW", 0);
    model.component("comp1").physics("gop").feature("relg1").setIndex("x0", "-1[mm]", 1);
    model.component("comp1").physics("gop").feature("relg1").set("RayDirectionVector", "Conical");
    model.component("comp1").physics("gop").feature("relg1").set("alphac", "0.2[deg]");
    model.component("comp1").physics("gop").feature("relg1").set("cax", new double[]{0, 1, 0});
    model.component("comp1").physics("gop").feature("relg1").set("InitialPolarizationType", "FullyPolarized");
    model.component("comp1").physics("gop").feature("relg1").set("axy0", 0);
    model.component("comp1").physics("gop").feature("relg1").set("az0", 1);
    model.component("comp1").physics("gop").feature("relg1").setIndex("Nw", 200, 0);
    model.component("comp1").physics("gop").feature("relg1").set("Psrc", "1[W/m]");

    model.component("comp1").mesh("mesh1").run();

    // ---- Ray-tracing study, sweep wavelength ----
    model.study().create("std1");
    model.study("std1").create("rtrac", "RayTracing");
    model.study("std1").feature("rtrac").set("tunit", "ps");
    model.study("std1").feature("rtrac").set("tlist", "range(0,50,2200)");
    // parametric sweep over wavelength
    model.study("std1").create("param", "Parametric");
    model.study("std1").feature("param").setIndex("pname", "lam", 0);
    model.study("std1").feature("param").setIndex("plistarr", "range(400,20,700)", 0);
    model.study("std1").feature("param").setIndex("punit", "nm", 0);
    model.study("std1").createAutoSequences("all");
    model.sol("sol1").runAll();

    // ---- Ray trajectory plot, coloured by wavelength ----
    model.result().dataset().create("ray1", "Ray");
    model.result().dataset("ray1").set("solution", "sol1");
    model.result().dataset("ray1").set("posdof", new String[]{"comp1.qx", "comp1.qy"});
    model.result().dataset("ray1").set("geom", "geom1");
    model.result().dataset("ray1").set("rgeom", "pgeom_gop");
    model.result().dataset("ray1").set("rgeomspec", "fromphysics");
    model.result().dataset("ray1").set("physicsinterface", "gop");
    model.result().create("pg1", "PlotGroup2D");
    model.result("pg1").set("data", "ray1");
    model.result("pg1").label("Ray Trajectories (ring 2D)");
    model.result("pg1").create("rtrj1", "RayTrajectories");
    model.result("pg1").feature("rtrj1").set("linetype", "line");
    model.result("pg1").feature("rtrj1").create("col1", "Color");
    model.result("pg1").feature("rtrj1").feature("col1").set("expr", "gop.lambda0");
    model.result("pg1").feature("rtrj1").feature("col1").set("unit", "nm");
    model.result("pg1").feature("rtrj1").create("filt1", "RayTrajectoriesFilter");

    model.label("ray_ring_2d.mph");
    return model;
  }
}
