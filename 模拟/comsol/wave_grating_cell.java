import com.comsol.model.*;
import com.comsol.model.util.*;

/**
 * Disc-spectrometer / ring-spectrum project - Wave Optics unit-cell model.
 *
 * One period of the disc track grating (rectangular grooves in a PC slab,
 * metalised, on air). A plane wave is incident from the air side; the Periodic
 * Structure feature adds a periodic port and Floquet conditions, and the
 * addDiffractionOrders command creates the individual diffraction orders so we
 * can read the +1 order efficiency and angle. Validated against the COMSOL
 * Application Library model hexagonal_grating (same feature pattern).
 *
 * Geometry (2D, extruded implicitly by ewfd in 2D):
 *   y in [0, gr_hpc]        : polycarbonate substrate (grooved top surface)
 *   y in [gr_hpc, gr_hpc+gr_h]   : metal layer fills the groove region
 *   y in [-gr_hair, 0]      : air (incident side, below)
 * The periodicity is along x with pitch d (track pitch).
 */
public class wave_grating_cell {

  public static void main(String[] args) {
    Model model = run();
    String out = "C:/Users/qiann/Desktop/TJPT鍏夋爡/妯℃嫙/comsol/wave_grating_cell.mph";
    try { model.save(out); } catch (Exception e) { System.out.println("SAVE_ERR " + e); }
    System.out.println("SAVED " + out);
  }

  public static Model run() {
    Model model = ModelUtil.create("Model");
    model.modelPath("C:/Users/qiann/Desktop/TJPT鍏夋爡/妯℃嫙/comsol");

    model.component().create("comp1", true);
    model.component("comp1").geom().create("geom1", 2);
    model.component("comp1").geom("geom1").geomRep("comsol");

    model.component("comp1").mesh().create("mesh1");

    model.component("comp1").physics().create("ewfd", "ElectromagneticWavesFrequencyDomain", "geom1");

    model.study().create("std1");
    model.study("std1").create("wave", "Wavelength");
    model.study("std1").feature("wave").set("ftplistmethod", "manual");
    model.study("std1").feature("wave").set("solnum", "auto");
    model.study("std1").feature("wave").set("notsolnum", "auto");
    model.study("std1").feature("wave").set("ngenAUX", "1");
    model.study("std1").feature("wave").set("goalngenAUX", "1");

    // ---- Parameters (DVD reference track) ----
    model.param().set("lda0", "0.55[um]", "vacuum wavelength (study overrides)");
    model.param().set("d", "0.74[um]", "track pitch (DVD)");
    model.param().set("w", "0.30[um]", "groove width");
    model.param().set("gr_h", "0.10[um]", "groove depth");
    model.param().set("gr_hpc", "0.40[um]", "PC layer thickness above grooves");
    model.param().set("gr_hair", "0.60[um]", "air height below grating");
    model.param().set("theta", "0[deg]", "incidence elevation angle from normal");
    model.param().set("n_pc", "1.58", "polycarbonate index");

    // Wavelength sweep 400-700 nm.
    model.study("std1").feature("wave").set("plist", "range(0.4[um],0.01[um],0.7[um])");

    model.component("comp1").geom("geom1").lengthUnit("um");

    // Air domain: x in [0,d], y in [-gr_hair,0]
    model.component("comp1").geom("geom1").create("r_air", "Rectangle");
    model.component("comp1").geom("geom1").feature("r_air").set("size", new String[]{"d", "gr_hair"});
    model.component("comp1").geom("geom1").feature("r_air").set("pos", new String[]{"0", "-gr_hair"});
    // PC domain above grooves: y in [gr_h, gr_h+gr_hpc]  (solid band)
    model.component("comp1").geom("geom1").create("r_pc", "Rectangle");
    model.component("comp1").geom("geom1").feature("r_pc").set("size", new String[]{"d", "gr_hpc"});
    model.component("comp1").geom("geom1").feature("r_pc").set("pos", new String[]{"0", "gr_h"});
    // Groove band y in [0,gr_h]: metal fills x in [0,w], PC fills x in [w,d]
    model.component("comp1").geom("geom1").create("r_met", "Rectangle");
    model.component("comp1").geom("geom1").feature("r_met").set("size", new String[]{"w", "gr_h"});
    model.component("comp1").geom("geom1").feature("r_met").set("pos", new String[]{"0", "0"});
    model.component("comp1").geom("geom1").create("r_pcg", "Rectangle");
    model.component("comp1").geom("geom1").feature("r_pcg").set("size", new String[]{"d-w", "gr_h"});
    model.component("comp1").geom("geom1").feature("r_pcg").set("pos", new String[]{"w", "0"});
    model.component("comp1").geom("geom1").run("fin");

    // ---- Selections for the periodic port boundaries (top & bottom) ----
    model.component("comp1").selection().create("sel_top", "Box");
    model.component("comp1").selection("sel_top").geom("geom1", 1);
    model.component("comp1").selection("sel_top").set("entitydim", "1");
    model.component("comp1").selection("sel_top").set("xmin", "-0.01*d");
    model.component("comp1").selection("sel_top").set("xmax", "1.01*d");
    model.component("comp1").selection("sel_top").set("ymin", "gr_h+gr_hpc-0.001");
    model.component("comp1").selection("sel_top").set("ymax", "gr_h+gr_hpc+0.001");
    model.component("comp1").selection().create("sel_bot", "Box");
    model.component("comp1").selection("sel_bot").geom("geom1", 1);
    model.component("comp1").selection("sel_bot").set("entitydim", "1");
    model.component("comp1").selection("sel_bot").set("xmin", "-0.01*d");
    model.component("comp1").selection("sel_bot").set("xmax", "1.01*d");
    model.component("comp1").selection("sel_bot").set("ymin", "-gr_hair-0.001");
    model.component("comp1").selection("sel_bot").set("ymax", "-gr_hair+0.001");

    // ---- Materials ----
    // Air (domain selection: the air rectangle)
    model.component("comp1").material().create("mat_air", "Common");
    model.component("comp1").material("mat_air").label("Air");
    model.component("comp1").material("mat_air").propertyGroup("def")
         .set("relpermittivity", new String[]{"1"});
    model.component("comp1").material("mat_air").propertyGroup("def")
         .set("relpermeability", new String[]{"1"});
    model.component("comp1").material("mat_air").propertyGroup("def")
         .set("electricconductivity", new String[]{"0"});
    model.component("comp1").material("mat_air").selection().set(new int[]{1});
    // Polycarbonate
    model.component("comp1").material().create("mat_pc", "Common");
    model.component("comp1").material("mat_pc").label("Polycarbonate");
    model.component("comp1").material("mat_pc").propertyGroup("def")
         .set("relpermittivity", new String[]{"n_pc^2"});
    model.component("comp1").material("mat_pc").propertyGroup("def")
         .set("relpermeability", new String[]{"1"});
    model.component("comp1").material("mat_pc").propertyGroup("def")
         .set("electricconductivity", new String[]{"0"});
    model.component("comp1").material("mat_pc").selection().set(new int[]{2, 4});
    // Metal (silver-like, lossy): use a large conductivity / complex n.
    model.component("comp1").material().create("mat_met", "Common");
    model.component("comp1").material("mat_met").label("Metal");
    model.component("comp1").material("mat_met").propertyGroup("def")
         .set("relpermittivity", new String[]{"1"});
    model.component("comp1").material("mat_met").propertyGroup("def")
         .set("relpermeability", new String[]{"1"});
    model.component("comp1").material("mat_met").propertyGroup("def")
         .set("electricconductivity", new String[]{"6.0e7[S/m]"});
    model.component("comp1").material("mat_met").selection().set(new int[]{3});

    // ---- Periodic Structure (adds periodic port + Floquet conditions) ----
    model.component("comp1").physics("ewfd").create("ps1", "PeriodicStructure", 2);
    model.component("comp1").physics("ewfd").feature("ps1").set("addListenerPort", false);
    model.component("comp1").physics("ewfd").feature("ps1").set("alpha1_inc", "theta");
    model.component("comp1").physics("ewfd").feature("ps1").set("alpha2_inc", "0");
    model.component("comp1").physics("ewfd").feature("ps1")
         .set("DiffractionOrderSpecification", "FromCurrentParameters");
    model.component("comp1").physics("ewfd").feature("ps1").feature("pport1")
         .runCommand("addDiffractionOrders");

    model.component("comp1").mesh("mesh1").run();

    model.study("std1").createAutoSequences("all");
    model.sol("sol1").runAll();

    // ---- Results: diffraction efficiency of each order ----
    model.result().create("pg1", "PlotGroup1D");
    model.result("pg1").set("data", "dset1");
    model.result("pg1").create("glob1", "Global");
    model.result("pg1").feature("glob1")
         .set("expr", new String[]{"ewfd.Rorder_0", "ewfd.Torder_0", "ewfd.Rtotal", "ewfd.Ttotal"});
    model.result("pg1").feature("glob1").set("xdata", "expr");
    model.result("pg1").feature("glob1").set("xdataexpr", "lambda0");
    model.result("pg1").feature("glob1").set("xdataunit", "nm");
    model.result("pg1").label("Diffraction orders");

    return model;
  }
}

