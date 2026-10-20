import com.comsol.model.*;
import com.comsol.model.util.*;

/** Read the solved 2D ring model and export the ray landing positions on the
 *  screen, then check rho = L*tan(beta) with sin(beta)=lambda/d. */
public class check_ring_2d {
  public static void main(String[] args) throws Exception {
    ModelUtil.clear();
    Model model = ModelUtil.load("m",
      "C:/Users/qiann/Desktop/TJPT光栅/模拟/comsol/ray_ring_2d_Model.mph");

    // Export ray trajectories (position + wavelength + diffraction order) at all times.
    model.result().export().create("data1", "Data");
    model.result().export("data1").set("data", "ray1");
    model.result().export("data1").set("expr", new String[]{"gop.lambda0"});
    model.result().export("data1").set("unit", new String[]{"nm"});
    model.result().export("data1").set("descr", new String[]{"wavelength"});
    model.result().export("data1").set("filename",
      "C:/Users/qiann/Desktop/TJPT光栅/模拟/comsol/ring_rays.txt");
    model.result().export("data1").run();
  }
}
