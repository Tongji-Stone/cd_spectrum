import com.comsol.model.*;
import com.comsol.model.util.*;

public class check_ring_3d {
  public static void main(String[] args) throws Exception {
    ModelUtil.clear();
    Model model = ModelUtil.load("m",
      "C:/Users/qiann/Desktop/TJPT光栅/模拟/comsol/ray_ring_3d_Model.mph");

    // export landing x, y, wavelength for all rays at all stored times
    model.result().export().create("data1", "Data");
    model.result().export("data1").set("data", "ray1");
    model.result().export("data1").set("expr", new String[]{"comp1.qx", "comp1.qy", "comp1.qz", "gop.lambda0"});
    model.result().export("data1").set("unit", new String[]{"mm", "mm", "mm", "nm"});
    model.result().export("data1").set("filename",
      "C:/Users/qiann/Desktop/TJPT光栅/模拟/comsol/ring3d_land.txt");
    model.result().export("data1").run();
  }
}
