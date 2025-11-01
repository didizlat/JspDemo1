package com.example.demo;

import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;

@Controller
public class FormController {

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
        
        // Success
        model.addAttribute("firstName", firstName);
        model.addAttribute("email", email);
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
        model.addAttribute("product", product);
        model.addAttribute("quantity", quantity);
        return "workflow-complete";
    }
}

