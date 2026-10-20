import com.comsol.model.*;
import com.comsol.model.util.*;

public class plot_ring_3d {
  public static void main(String[] args) throws Exception {
    ModelUtil.clear();
    Model model = ModelUtil.load("m",
      "C:/Users/qiann/Desktop/TJPT光栅/模拟/comsol/ray_ring_3d_Model.mph");
    model.result("pg1").run();

    // side view (default 3D camera)
    model.result().export().create("img1", "Image");
    model.result().export("img1").set("plotgroup", "pg1");
    model.result().export("img1").set("pngfilename",
      "C:/Users/qiann/Desktop/TJPT光栅/模拟/comsol/ring_3d.png");
    model.result().export("img1").set("size", "manualweb");
    model.result().export("img1").set("unit", "px");
    model.result().export("img1").set("height", "800");
    model.result().export("img1").set("width", "1000");
    model.result().export("img1").run();

    // screen hit pattern: use a filter to keep only the last point (on screen)
    // render a top-down view by setting the default view camera to look down -z
    model.result("pg1").set("view", "view1");
    try {
      model.result().export().create("img2", "Image");
      model.result().export("img2").set("plotgroup", "pg1");
      model.result().export("img2").set("pngfilename",
        "C:/Users/qiann/Desktop/TJPT光栅/模拟/comsol/ring_3d_top.png");
      model.result().export("img2").set("size", "manualweb");
      model.result().export("img2").set("unit", "px");
      model.result().export("img2").set("height", "900");
      model.result().export("img2").set("width", "900");
      model.result().export("img2").run();
    } catch (Exception e) { }
  }
}
