/**
 * Test Case 06: JavaScript Temporal Dead Zone / Scope Error
 * Expected Error: ReferenceError: Cannot access 'calculatedDiscount' before initialization
 * Testing: Can Tesseract detect JS lexical block scoping and TDZ bugs?
 */

function calculateFinalPrice(basePrice, isMember) {
    if (isMember) {
        console.log("Applying member discount:", calculatedDiscount); // TDZ Bug!
        let calculatedDiscount = basePrice * 0.15;
        return basePrice - calculatedDiscount;
    }
    return basePrice;
}

calculateFinalPrice(100, true);
