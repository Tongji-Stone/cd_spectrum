import com.comsol.model.*;
import com.comsol.model.util.*;

/**
 * Ring-spectrum project - 3D Ray Optics model of the annular spectrum.
 *
 * Geometry (transmission layout, source and screen on opposite sides of disc):
 *   - Disc (the circular track grating) lies in the plane z = 0.
 *   - Collimated light travels along the disc axis (+z) from below.
 *   - The screen sits at z = L, with a central hole that lets the incident beam
 *     pass and the zero order through; the +1 order of each wavelength forms a
 *     cone of half-angle beta (sin beta = lambda/d) that lands as a ring of
 *     radius rho = L*tan(beta) on the screen.
 *   - The grooves run tangentially; the grating periodicity is radial, which is
 *     why a normally-incident ray is diffracted radially outward into a cone.
 *
 * Polychromatic release: every released ray carries a different vacuum
 * wavelength sampled uniformly in [lambda0min, lambda0max], so one solve gives
 * the whole set of rings.
 */
public class ray_ring_3d {

  public static void main(String[] args) {
    Model model = run();
    String out = "C:/Users/qiann/Desktop/TJPT光栅/模拟/comsol/ray_ring_3d.mph";
    try { model.save(out); } catch (Exception e) { }
  }

  public static Model run() {
    Model model = ModelUtil.create("Model");
    model.modelPath("C:/Users/qiann/Desktop/TJPT光栅/模拟/comsol");

    // ---- parameters ----
    model.param().set("d", "0.74[um]", "track pitch (DVD)");
    model.param().set("L", "100[mm]", "disc-to-screen distance");
    model.param().set("Rdisc", "40[mm]", "disc grating radius (illuminated)");
    model.param().set("Rscr", "320[mm]", "screen outer radius");
    model.param().set("Rhole", "15[mm]", "screen central hole radius");
    model.param().set("Rbeam", "12[mm]", "incident beam radius");
    model.param().set("lambda0min", "400[nm]", "min wavelength");
    model.param().set("lambda0max", "700[nm]", "max wavelength");
    model.param().set("Rfix", "0.35", "fixed order reflectance (placeholder)");

    model.component().create("comp1", true);
    model.component("comp1").geom().create("geom1", 3);
    model.component("comp1").geom("geom1").lengthUnit("mm");
    model.component("comp1").mesh().create("mesh1");

    // Propagation volume: a cylinder of air from z=-10 to z=L+5.
    model.component("comp1").geom("geom1").create("cyl1", "Cylinder");
    model.component("comp1").geom("geom1").feature("cyl1").set("r", "Rscr");
    model.component("comp1").geom("geom1").feature("cyl1").set("h", "L+15[mm]");
    model.component("comp1").geom("geom1").feature("cyl1").set("pos", new String[]{"0", "0", "-10[mm]"});
    // Disc grating: a circular work plane at z=0, used as an interior boundary.
    model.component("comp1").geom("geom1").create("wp1", "WorkPlane");
    model.component("comp1").geom("geom1").feature("wp1").set("quickz", "0");
    model.component("comp1").geom("geom1").feature("wp1").set("unite", false);
    model.component("comp1").geom("geom1").feature("wp1").geom().create("c1", "Circle");
    model.component("comp1").geom("geom1").feature("wp1").geom().feature("c1").set("r", "Rdisc");
    model.component("comp1").geom("geom1").run("wp1");
    // Screen: annular face at z=L (outer Rscr, inner hole Rhole) as interior boundary.
    model.component("comp1").geom("geom1").create("wp2", "WorkPlane");
    model.component("comp1").geom("geom1").feature("wp2").set("quickz", "L");
    model.component("comp1").geom("geom1").feature("wp2").set("unite", false);
    model.component("comp1").geom("geom1").feature("wp2").geom().create("c2", "Circle");
    model.component("comp1").geom("geom1").feature("wp2").geom().feature("c2").set("r", "Rscr");
    model.component("comp1").geom("geom1").feature("wp2").geom().create("c3", "Circle");
    model.component("comp1").geom("geom1").feature("wp2").geom().feature("c3").set("r", "Rhole");
    model.component("comp1").geom("geom1").feature("wp2").geom().create("dif1", "Difference");
    model.component("comp1").geom("geom1").feature("wp2").geom().feature("dif1").selection("input").set("c2");
    model.component("comp1").geom("geom1").feature("wp2").geom().feature("dif1").selection("input2").set("c3");
    model.component("comp1").geom("geom1").run("wp2");
    model.component("comp1").geom("geom1").run("fin");

    // ---- air material ----
    model.component("comp1").material().create("mat1", "Common");
    model.component("comp1").material("mat1").propertyGroup("def").set("relpermittivity", new String[]{"1"});
    model.component("comp1").material("mat1").propertyGroup("def").set("relpermeability", new String[]{"1"});
    model.component("comp1").material("mat1").propertyGroup("def").set("electricconductivity", new String[]{"0"});
    model.component("comp1").material("mat1").selection().all();

    // ---- Geometrical Optics ----
    model.component("comp1").physics().create("gop", "GeometricalOptics", "geom1");
    model.component("comp1").physics("gop").prop("IntensityComputation")
         .setIndex("IntensityComputation", "ComputeIntensity", 0);
    model.component("comp1").physics("gop").prop("MaximumSecondary")
         .setIndex("MaximumSecondary", 50000, 0);
    model.component("comp1").physics("gop").prop("WavelengthDistribution")
         .setIndex("WavelengthDistribution", "PolychromaticWavelength", 0);
    model.component("comp1").physics("gop").feature("op1")
         .set("RayPropertySpecification", "SpecifyVacuumWavelength");
    model.component("comp1").physics("gop").feature("op1").set("lambda0", "lambda0min");

    // Grating on the disc face (work plane wp1 -> boundary). Periodicity radial.
    model.component("comp1").physics("gop").create("grat1", "Grating", 2);
    model.component("comp1").physics("gop").feature("grat1").selection().geom("geom1", 2);
    // select the disc boundary via a box selection
    model.component("comp1").selection().create("sel_grat", "Box");
    model.component("comp1").selection("sel_grat").geom("geom1", 2);
    model.component("comp1").selection("sel_grat").set("entitydim", "2");
    model.component("comp1").selection("sel_grat").set("xmin", "-Rdisc-1");
    model.component("comp1").selection("sel_grat").set("xmax", "Rdisc+1");
    model.component("comp1").selection("sel_grat").set("ymin", "-Rdisc-1");
    model.component("comp1").selection("sel_grat").set("ymax", "Rdisc+1");
    model.component("comp1").selection("sel_grat").set("zmin", "-0.5");
    model.component("comp1").selection("sel_grat").set("zmax", "0.5");
    model.component("comp1").physics("gop").feature("grat1").selection().named("sel_grat");
    model.component("comp1").physics("gop").feature("grat1").set("dg", "d");
    model.component("comp1").physics("gop").feature("grat1").set("RaysToRelease", "Transmitted");
    // grooves tangential => periodicity radial = (x, y, 0)/r. Try user-defined vector.
    // radial periodicity vector (unit), grooves tangential. Tgp = periodicity dir.
    model.component("comp1").physics("gop").feature("grat1").set("DirectionOfPeriodicity", "UserDefined");
    model.component("comp1").physics("gop").feature("grat1")
         .set("Tgp", new String[]{"x/sqrt(x^2+y^2+1e-30)", "y/sqrt(x^2+y^2+1e-30)", "0"});
    model.component("comp1").physics("gop").feature("grat1")
         .set("Tgl", new String[]{"-y/sqrt(x^2+y^2+1e-30)", "x/sqrt(x^2+y^2+1e-30)", "0"});
    // orders: 0 and +1 transmitted
    model.component("comp1").physics("gop").feature("grat1").feature("dfo1").set("mg", 0);
    model.component("comp1").physics("gop").feature("grat1").feature("dfo1").set("Rf", "0");
    model.component("comp1").physics("gop").feature("grat1").feature("dfo1").set("Tr", "1");
    model.component("comp1").physics("gop").feature("grat1").create("dfo2", "DiffractionOrder", 2);
    model.component("comp1").physics("gop").feature("grat1").feature("dfo2").set("mg", 1);
    model.component("comp1").physics("gop").feature("grat1").feature("dfo2").set("Rf", "0");
    model.component("comp1").physics("gop").feature("grat1").feature("dfo2").set("Tr", "1");

    // Screen: annular wall that freezes rays
    model.component("comp1").selection().create("sel_scr", "Box");
    model.component("comp1").selection("sel_scr").geom("geom1", 2);
    model.component("comp1").selection("sel_scr").set("entitydim", "2");
    model.component("comp1").selection("sel_scr").set("xmin", "-Rscr-1");
    model.component("comp1").selection("sel_scr").set("xmax", "Rscr+1");
    model.component("comp1").selection("sel_scr").set("ymin", "-Rscr-1");
    model.component("comp1").selection("sel_scr").set("ymax", "Rscr+1");
    model.component("comp1").selection("sel_scr").set("zmin", "L-0.5");
    model.component("comp1").selection("sel_scr").set("zmax", "L+0.5");
    model.component("comp1").physics("gop").create("wall1", "Wall", 2);
    model.component("comp1").physics("gop").feature("wall1").selection().named("sel_scr");
    model.component("comp1").physics("gop").feature("wall1").set("WallCondition", "Freeze");

    // Polychromatic collimated release: disc of rays below disc, going +z.
    model.component("comp1").physics("gop").create("relg1", "ReleaseGrid", -1);
    model.component("comp1").physics("gop").feature("relg1").setIndex("x0", "0", 0);
    model.component("comp1").physics("gop").feature("relg1").setIndex("x0", "0", 1);
    model.component("comp1").physics("gop").feature("relg1").setIndex("x0", "-8[mm]", 2);
    model.component("comp1").physics("gop").feature("relg1").set("RayDirectionVector", "Conical");
    model.component("comp1").physics("gop").feature("relg1").set("cax", new double[]{0, 0, 1});
    model.component("comp1").physics("gop").feature("relg1").set("alphac", "0.2[deg]");
    model.component("comp1").physics("gop").feature("relg1").setIndex("Nw", 400, 0);
    model.component("comp1").physics("gop").feature("relg1").set("Rc", "Rbeam");
    model.component("comp1").physics("gop").feature("relg1").set("InitialPolarizationType", "FullyPolarized");
    model.component("comp1").physics("gop").feature("relg1").set("axy0", 0);
    model.component("comp1").physics("gop").feature("relg1").set("az0", 1);
    // polychromatic
    model.component("comp1").physics("gop").feature("relg1").set("LDistributionFunction", "Uniform");
    model.component("comp1").physics("gop").feature("relg1").setIndex("lambda0Nval", 25, 0);
    model.component("comp1").physics("gop").feature("relg1").set("lambda0min", "lambda0min");
    model.component("comp1").physics("gop").feature("relg1").set("lambda0max", "lambda0max");

    model.component("comp1").mesh("mesh1").run();

    // ---- ray tracing study ----
    model.study().create("std1");
    model.study("std1").create("rtrac", "RayTracing");
    model.study("std1").feature("rtrac").set("tunit", "ps");
    model.study("std1").feature("rtrac").set("tlist", "range(0,100,3000)");
    model.study("std1").createAutoSequences("all");
    model.sol("sol1").runAll();

    // ---- 3D trajectory plot, rays coloured by wavelength ----
    model.result().dataset().create("ray1", "Ray");
    model.result().dataset("ray1").set("solution", "sol1");
    model.result().dataset("ray1").set("posdof", new String[]{"comp1.qx", "comp1.qy", "comp1.qz"});
    model.result().dataset("ray1").set("geom", "geom1");
    model.result().dataset("ray1").set("rgeom", "pgeom_gop");
    model.result().dataset("ray1").set("rgeomspec", "fromphysics");
    model.result().dataset("ray1").set("physicsinterface", "gop");
    model.result().create("pg1", "PlotGroup3D");
    model.result("pg1").set("data", "ray1");
    model.result("pg1").label("Ring spectrum trajectories");
    model.result("pg1").create("rtrj1", "RayTrajectories");
    model.result("pg1").feature("rtrj1").set("linetype", "line");
    model.result("pg1").feature("rtrj1").create("col1", "Color");
    model.result("pg1").feature("rtrj1").feature("col1").set("expr", "gop.lambda0");
    model.result("pg1").feature("rtrj1").feature("col1").set("unit", "nm");
    model.result("pg1").feature("rtrj1").create("filt1", "RayTrajectoriesFilter");

    model.label("ray_ring_3d.mph");
    return model;
  }
}
