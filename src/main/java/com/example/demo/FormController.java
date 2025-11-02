package com.example.demo;

import com.example.demo.entity.Order;
import com.example.demo.entity.Registration;
import com.example.demo.repository.OrderRepository;
import com.example.demo.repository.RegistrationRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;

import java.time.LocalDate;

@Controller
public class FormController {

    @Autowired
    private RegistrationRepository registrationRepository;
    
    @Autowired
    private OrderRepository orderRepository;

    @GetMapping("/registration")
    public String registrationForm() {
        return "registration";
    }

    @PostMapping("/registration")
    public String submitRegistration(
            @RequestParam(required = false) String firstName,
            @RequestParam(required = false) String lastName,
            @RequestParam(required = false) String email,
            @RequestParam(required = false) String phone,
            @RequestParam(required = false) String birthdate,
            @RequestParam(required = false) String gender,
            @RequestParam(required = false) String country,
            @RequestParam(required = false) String[] interests,
            @RequestParam(required = false) String newsletter,
            @RequestParam(required = false) String comments,
            Model model) {
        
        // Validation
        if (firstName == null || firstName.trim().isEmpty()) {
            model.addAttribute("error", "First name is required");
            return "registration";
        }
        if (email == null || email.trim().isEmpty() || !email.contains("@")) {
            model.addAttribute("error", "Valid email is required");
            return "registration";
        }
        
        // Save to database
        Registration registration = new Registration();
        registration.setFirstName(firstName);
        registration.setLastName(lastName);
        registration.setEmail(email);
        registration.setPhone(phone);
        
        if (birthdate != null && !birthdate.trim().isEmpty()) {
            try {
                registration.setBirthdate(LocalDate.parse(birthdate));
            } catch (Exception e) {
                // ignore invalid dates
            }
        }
        
        registration.setGender(gender);
        registration.setCountry(country);
        
        if (interests != null && interests.length > 0) {
            registration.setInterests(String.join(", ", interests));
        }
        
        registration.setComments(comments);
        registration.setNewsletter("yes".equals(newsletter));
        
        Registration saved = registrationRepository.save(registration);
        
        // Redirect to success page to prevent form resubmission
        return "redirect:/registration/success?id=" + saved.getId();
    }
    
    @GetMapping("/registration/success")
    public String registrationSuccess(@RequestParam Long id, Model model) {
        Registration registration = registrationRepository.findById(id).orElse(null);
        if (registration != null) {
            model.addAttribute("firstName", registration.getFirstName());
            model.addAttribute("email", registration.getEmail());
            model.addAttribute("registrationId", id);
        }
        return "registration-success";
    }

    @GetMapping("/workflow")
    public String workflowStart() {
        return "workflow-step1";
    }

    @PostMapping("/workflow/step2")
    public String workflowStep2(@RequestParam(required = false) String product, Model model) {
        if (product == null || product.trim().isEmpty()) {
            model.addAttribute("error", "Please select a product");
            return "workflow-step1";
        }
        model.addAttribute("product", product);
        return "workflow-step2";
    }

    @PostMapping("/workflow/step3")
    public String workflowStep3(@RequestParam String product, @RequestParam(required = false) String quantity, Model model) {
        if (quantity == null || quantity.trim().isEmpty()) {
            model.addAttribute("error", "Please enter quantity");
            model.addAttribute("product", product);
            return "workflow-step2";
        }
        try {
            int qty = Integer.parseInt(quantity);
            if (qty < 1) {
                model.addAttribute("error", "Quantity must be at least 1");
                model.addAttribute("product", product);
                return "workflow-step2";
            }
        } catch (NumberFormatException e) {
            model.addAttribute("error", "Please enter a valid number");
            model.addAttribute("product", product);
            return "workflow-step2";
        }
        model.addAttribute("product", product);
        model.addAttribute("quantity", quantity);
        return "workflow-step3";
    }

    @PostMapping("/workflow/complete")
    public String workflowComplete(@RequestParam String product, @RequestParam String quantity, Model model) {
        // Save order to database
        Order order = new Order();
        order.setProduct(product);
        order.setQuantity(Integer.parseInt(quantity));
        Order saved = orderRepository.save(order);
        
        // Redirect to success page
        return "redirect:/workflow/complete?id=" + saved.getId();
    }
    
    @GetMapping("/workflow/complete")
    public String workflowCompleteSuccess(@RequestParam Long id, Model model) {
        Order order = orderRepository.findById(id).orElse(null);
        if (order != null) {
            model.addAttribute("product", order.getProduct());
            model.addAttribute("quantity", order.getQuantity());
            model.addAttribute("orderNumber", order.getOrderNumber());
            model.addAttribute("orderId", order.getId());
        }
        return "workflow-complete";
    }
    
    @GetMapping("/admin/registrations")
    public String viewRegistrations(Model model) {
        model.addAttribute("registrations", registrationRepository.findByOrderByRegisteredAtDesc());
        return "admin-registrations";
    }
    
    @GetMapping("/admin/orders")
    public String viewOrders(Model model) {
        model.addAttribute("orders", orderRepository.findByOrderByOrderedAtDesc());
        return "admin-orders";
    }
}

