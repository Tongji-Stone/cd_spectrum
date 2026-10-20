import com.comsol.model.*;
import com.comsol.model.util.*;

public class check_landing {
  public static void main(String[] args) throws Exception {
    ModelUtil.clear();
    Model model = ModelUtil.load("m",
      "C:/Users/qiann/Desktop/TJPT光栅/模拟/comsol/ray_ring_2d_Model.mph");

    // export x-position of rays and their wavelength at final time
    model.result().export().create("data1", "Data");
    model.result().export("data1").set("data", "ray1");
    model.result().export("data1").set("expr", new String[]{"comp1.qx", "gop.lambda0"});
    model.result().export("data1").set("unit", new String[]{"mm", "nm"});
    model.result().export("data1").set("filename",
      "C:/Users/qiann/Desktop/TJPT光栅/模拟/comsol/landing.txt");
    model.result().export("data1").run();
  }
}
